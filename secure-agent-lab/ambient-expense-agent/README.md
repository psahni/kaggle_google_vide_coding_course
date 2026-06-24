# ambient-expense-agent

Simple ReAct agent
Agent generated with `agents-cli` version `0.5.0`

## Project Structure

```
ambient-expense-agent/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── agent_runtime_app.py    # Agent Runtime application logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli publish gemini-enterprise` | Register deployed agent to Gemini Enterprise                    |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.



## About Project Structure


Viewed test_pubsub.py:35-63
Listed directory app
Listed directory expense_agent
Viewed main.py:1-122
Viewed agent_runtime_app.py:1-73
Viewed agent.py:1-80
Viewed agent.py:1-111

Here is an overview of the project structure and the rationale behind separating the `expense_agent` and `app` folders.

---

### **Project Structure Overview**
```
ambient-expense-agent/
├── app/                      # The Hosting / Runtime Layer (FastAPI, GCP integration)
│   ├── main.py               # FastAPI server exposing HTTP webhooks and endpoints
│   ├── agent.py              # Root fallback agent setup
│   └── agent_runtime_app.py  # Telemetry, GCS logging, and Vertex AI Agent Engine setup
│
├── expense_agent/            # The Core Business Logic Layer (The Agent Graph Workflow)
│   ├── models.py             # Pydantic schemas representing domain models (ExpenseReport, etc.)
│   ├── nodes.py              # Individual workflow step functions (parsing, security, review)
│   ├── agent.py              # Wiring of function nodes into a Workflow graph using ADK
│   └── config.py             # Domain-specific configurations (amount threshold, model name)
```

---

### **Why are they separated?**

#### **1. Separation of Concerns & Modular Architecture**
* **`expense_agent/` is the Core Domain Logic:** This directory contains the business rules, step-by-step logic, and graph wiring. It is completely runtime-agnostic. It does not care *how* it is invoked—whether via a web server, a command-line tool (CLI), a Python unit test, or an interactive chat playground.
* **`app/` is the Hosting & Delivery Layer:** This directory manages execution endpoints, FastAPI integration, Google Cloud (GCP/Vertex AI) setup, authentication, and HTTP request/response payloads.

#### **2. Support for Multiple Entry Points**
By separating the core workflow graph, different environments can load it differently:
* **Production/Ambient API:** [app/main.py](file:///e:/Prashant/development/2026/ag2-projects/secure-agent-lab/ambient-expense-agent/app/main.py) loads the graph to run as an event-driven webhook backend responding to GCP Pub/Sub push messages.
* **Interactive Development (Playground):** Running `make playground` starts the ADK Web UI, which interacts with the exported workflow graph in [expense_agent/agent.py](file:///e:/Prashant/development/2026/ag2-projects/secure-agent-lab/ambient-expense-agent/expense_agent/agent.py) to provide a chat interface.

#### **3. Testability**
Because [expense_agent/](file:///e:/Prashant/development/2026/ag2-projects/secure-agent-lab/ambient-expense-agent/expense_agent/) has no web server or deployment-specific dependencies, you can easily run local unit and integration tests against individual nodes or the workflow runner without spinning up a web server.
