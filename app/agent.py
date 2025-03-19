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
from google.cloud import trace_v1
from datetime import datetime, timedelta, timezone

load_dotenv()

LOCATION = "us-central1"
LLM = "gemini-2.0-flash-001"

system_message = """
You are a monitoring agent in charge of checking the logs of a deployed environment.
When asked to, you should query the recent logs (last 24h) of a GCP environment and check if any error is present.
When such an error is present and feature an easily identifiable file, you will search this file in its Github repository, find the line of error and propose a fix to the user.
"""

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
GCP_PROJECT_NAME = os.environ.get("GCP_PROJECT_NAME")
CLOUD_RUN_NAME = os.environ.get("CLOUD_RUN_NAME")

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
def check_gcp_traces(start_time: str, end_time: str) -> str:
    """Check GCP traces for anomalies and return relevant details."""
    client = trace_v1.TraceServiceClient()

    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

    request = trace_v1.ListTracesRequest(
        project_id=GCP_PROJECT_NAME,
        start_time=start_time,
        end_time=end_time,
    )

    traces = client.list_traces(request=request)
    traces_str = str(traces)

    if "error" in traces_str.lower() or "exception" in traces_str.lower():
        send_slack_alert(traces_str)

    return traces_str


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
    auth = Auth.Token("access_token")
    g = Github(auth=auth)
    repo = g.get_repo("dashq-norma/dashq-api-service")
    file_content = repo.get_contents(relative_path, ref="dev")
    g.close()
    return file_content.decoded_content.decode("utf-8")


tools = [get_gcp_logs, check_gcp_traces, query_github_file]

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
                               {"type": "system", "content": system_message},
                               {"type": "system", "content": f"The current date is {datetime.now().strftime('%Y-%m-%d')}."},
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
