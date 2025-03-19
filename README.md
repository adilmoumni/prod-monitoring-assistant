# prod-monitoring-assistant

A agent implementing a base ReAct agent using LangGraph

Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack)


## Project Overview

**Prod Monitoring Assistant** is an intelligent agent that helps **monitor production environments**, **analyze logs**, and **detect issues** in real time. It provides actionable insights and assists developers with debugging through an interactive **Slack bot** and **API interface**.

### Key Features

✅ **Automated Issue Detection** – Analyzes logs, traces, and recent code changes to pinpoint root causes.  
✅ **Slack Bot Integration** – Developers can interact with the agent via Slack for real-time troubleshooting.  
✅ **Production Monitoring** – Monitors multiple production environments 24/7, ensuring continuous uptime.  
✅ **FastAPI Backend** – Serves as the core interface for communication between the agent, the frontend, and external integrations.  
✅ **Cloud-Native Deployment** – Uses Terraform for infrastructure as code and Google Cloud services for scalability.  

---

## How It Works

1. **Monitor Production Logs** – The agent continuously analyzes logs and traces to detect anomalies.  
2. **Identify Issues** – Using AI, it identifies potential root causes, such as failed API calls, incorrect schema validation, or resource exhaustion.  
3. **Explain & Suggest Fixes** – The agent provides detailed explanations of detected errors and recommends debugging steps.  
4. **Interact via Slack** – Developers can chat with the agent in Slack to request insights and troubleshooting steps.  
5. **Improve Over Time** – The system continuously learns from past issues to provide better recommendations.  


## Project Structure

This project is organized as follows:

```
prod-monitoring-assistant/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── server.py        # FastAPI Backend server
│   └── utils/           # Utility functions and helpers
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
└── pyproject.toml       # Project dependencies and configuration
```

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


### Installation

Install required packages using uv:

```bash
make install
```

### Setup

If not done during the initialization, set your default Google Cloud project and Location:

```bash
export PROJECT_ID="qwiklabs-gcp-03-98e7977f8112"
export LOCATION="us-central1"
gcloud config set project $PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch local development environment with backend and frontend |
| `make backend`       | Start backend server only |
| `make ui`            | Launch Streamlit frontend without local backend |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |
| `uv run jupyter lab` | Launch Jupyter notebook                                                                     |

For full command options and usage, refer to the [Makefile](Makefile).


## Usage

1. **Prototype:** Build your Generative AI Agent using the intro notebooks in `notebooks/` for guidance. Use Vertex AI Evaluation to assess performance.
2. **Integrate:** Import your chain into the app by editing `app/agent.py`.
3. **Test:** Explore your chain's functionality using the Streamlit playground with `make playground`. The playground offers features like chat history, user feedback, and various input types, and automatically reloads your agent on code changes.
4. **Deploy:** Configure and trigger the CI/CD pipelines, editing tests if needed. See the [deployment section](#deployment) for details.
5. **Monitor:** Track performance and gather insights using Cloud Logging, Tracing, and the Looker Studio dashboard to iterate on your application.


## Deployment

### Dev Environment

The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.

## Monitoring and Observability

>> You can use [this Looker Studio dashboard](https://lookerstudio.google.com/c/reporting/fa742264-4b4b-4c56-81e6-a667dd0f853f/page/tEnnC) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to getting started.

The application uses OpenTelemetry for comprehensive observability with all events being sent to Google Cloud Trace and Logging for monitoring and to BigQuery for long term storage. 
