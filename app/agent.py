# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from google.cloud.trace_v1 import ListTracesRequest
# mypy: disable-error-code="union-attr"
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from google.cloud import logging
from github import Github
from github import Auth
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

LOCATION = "us-central1"
LLM = "gemini-2.0-flash-001"

system_message = f"""
You are an advanced production monitoring agent responsible for overseeing our deployed environment. Your tasks include:

1. Querying logs and traces from the past 24 hours—do not look beyond this period.
2. Answer questions such as:
   - "Can you give me the list of calls we had in the Cloud Run service in the last 12 hours?"
   - "What was the last issue faced?"
   - "Analyze the logs and traces to determine which part of the project’s code might be the root cause."
3. For any incident detected:
   - Extract key details (error messages, timestamps, etc.) from logs and traces.
   - Identify if the error references a specific source file.
   - If a file is referenced, search the corresponding Github repository to locate the relevant code.
   - Identify the specific code line(s) that might be causing the issue.
   - Propose a concise, actionable fix based on your analysis.
4. If no anomalies or errors are found, confirm that the system is operating normally.

Always include relevant context (e.g., error details, affected file names) in your responses and ensure that the timeframe does not exceed 24 hours.
Current date and time (Europe/Paris): {datetime.now(ZoneInfo("Europe/Paris")).strftime('%Y-%m-%d %H:%M')}
"""

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
GCP_PROJECT_NAME = os.environ.get("GCP_PROJECT_NAME")
CLOUD_RUN_NAME = os.environ.get("CLOUD_RUN_NAME")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

# 1. Create an alert context
# severity="DEFAULT" should be switch to "ERROR" in prod.
def send_slack_alert(error_logs, severity="DEFAULT", dry_run=False):
    """Sends an error message with GCP logs."""

    payload = {
        "attachments": [
            {
                "fallback": f"*{severity} in production",
                "text": f"```{error_logs}```",

            }
        ]
    }

    if dry_run:
        print("[Test] Slack alert:", json.dumps(payload, indent=2))
        return

    headers = {"Content-Type": "application/json"}
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers=headers)

    if response.status_code != 200:
        print(f"Error while sending message to Slack: {response.text}")


# 2. Define tools
@tool
def get_gcp_logs(start_time: str, end_time: str) -> str:
    """
    Get app logs within a specified timestamp range.

    Args:
        start_time (datetime): The start time (inclusive) for the log query in UTC.
        end_time (datetime): The end time (exclusive) for the log query in UTC.

    Returns:
        str: A string representation of the retrieved log entries.
    """

    # Convert start_time and end_time to datetime objects if they are provided as strings.

    # Initialize the client
    client = logging.Client()

    # Define a filter for Cloud Run logs with a timestamp range.
    # Note: Ensure start_time and end_time are timezone-aware or in UTC.
    filter_str = (
        f'resource.labels.service_name="{CLOUD_RUN_NAME}" '
        f'AND timestamp >= "{start_time}" '
        f'AND timestamp < "{end_time}"'
    )

    # List log entries using the filter
    entries = list(client.list_entries(filter_=filter_str))

    return str(entries)


@tool
def query_github_file(
        relative_path: str
) -> str:
    """Get the code source of a files on the GitHub repository."""
    print('==================== GET GITHUB FILE ====================')
    print(relative_path)
    auth = Auth.Token(ACCESS_TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo("dashq-norma/dashq-api-service")
    file_content = repo.get_contents(relative_path, ref="dev")
    g.close()
    return file_content.decoded_content.decode("utf-8")


@tool
def search_github_repo(query: str) -> str:
    """
    Search the GitHub repository for files matching the query.
    Args:
        query (str): A keyword or regex pattern to filter file names.
    Returns:
        str: A list of file paths (as a string) that match the query.
    """
    auth = Auth.Token(ACCESS_TOKEN)
    g = Github(auth=auth)
    try:
        repo = g.get_repo("dashq-norma/dashq-api-service")
        # Retrieve the entire repository tree (you may need to adjust branch as needed)
        tree = repo.get_git_tree("main", recursive=True)
        matching_files = [file.path for file in tree.tree if query.lower() in file.path.lower()]
        return json.dumps(matching_files, indent=2)
    except Exception as e:
        return f"GitHub repository search error: {e}"
    finally:
        g.close()
        
@tool
def search_github_code(query: str) -> str:
    """
    Searches the GitHub repository for files containing the specified query string.
    Args:
        query (str): The keyword or phrase to search within file contents.
    Returns:
        str: A JSON-formatted list of matching file paths and code snippets.
    """
    try:
        headers = {"Authorization": f"token {ACCESS_TOKEN}"}
        search_url = "https://api.github.com/search/code"
        # The 'q' parameter combines the query with the repository qualifier.
        params = {
            "q": f"{query} repo:dashq-norma/dashq-api-service",
            "per_page": 10
        }
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code != 200:
            return f"GitHub code search error: {response.text}"
        results = response.json()
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Exception during GitHub code search: {e}"

tools = [get_gcp_logs, query_github_file, search_github_repo, search_github_code]

# 3. Set up the language model
llm = ChatVertexAI(
    model=LLM, location=LOCATION, temperature=0, max_tokens=1024, streaming=True
).bind_tools(tools)


# 4. Define workflow components
def should_continue(state: MessagesState) -> str:
    """Determines whether to use tools or end the conversation."""
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END


def call_model(state: MessagesState, config: RunnableConfig) -> dict[str, BaseMessage]:
    """Calls the language model and returns the response."""
    messages_with_system = [
                               {"type": "system", "content": system_message}
                           ] + state[
        "messages"
    ]
    # Forward the RunnableConfig object to ensure the agent is capable of streaming the response.
    response = llm.invoke(messages_with_system, config)
    return {"messages": response}


# 5. Create the workflow graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")

# 6. Define graph edges
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# 7. Compile the workflow
agent = workflow.compile()
