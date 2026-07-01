# 💻 IT Support Laptop Lifecycle Agent

Simple ReAct agent
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.41.3`

## 📁 Project Structure

```
it-support-agent/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── agent_engine_app.py    # Agent Engine application logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
├── Makefile                   # Development commands
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## 📋 Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## ⚡ Quick Start

Install required packages and launch the local development environment:

```bash
make install && make playground
```

## ⚙️ Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install dependencies using uv                                                               |
| `make playground`    | Launch local development environment                                                        |
| `make lint`          | Run code quality checks                                                                     |
| `make test`          | Run unit and integration tests                                                              |
| `make deploy`        | Deploy agent to Agent Engine                                                                |
| `make register-gemini-enterprise` | Register deployed agent to Gemini Enterprise                                  |

For full command options and usage, refer to the [Makefile](Makefile).

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `uvx agent-starter-pack enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `uvx agent-starter-pack setup-cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `uvx agent-starter-pack upgrade` | Auto-upgrade to latest version while preserving customizations |
| `uvx agent-starter-pack extract` | Extract minimal, shareable version of your agent |

---



## 🌐 Next.js Web Portal Connection
The Next.js frontend application connects directly to the Firestore database to serve the ticket dashboard and process approvals.

* **SDK/Driver**: Utilizes the `firebase-admin` Node.js library for secure, server-side database connectivity.
* **Initialization**: Configured in [db.ts](frontend/lib/db.ts) using the target GCP Project ID.
* **Environment Variables**: Reads `GOOGLE_CLOUD_PROJECT` to determine the target database. When deployed on Google Cloud Run, it automatically inherits permissions from the runtime's service account to query Firestore without local credential JSON files.



## 🛠️ Development

Edit your agent logic in `app/agent.py` and test with `make playground` - it auto-reloads on save.
See the [development guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/development-guide) for the full workflow.

## 🚀 Deployment

```bash
gcloud config set project <your-project-id>
make deploy
```

To add CI/CD and Terraform, run `uvx agent-starter-pack enhance`.
To set up your production infrastructure, run `uvx agent-starter-pack setup-cicd`.
See the [deployment guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment) for details.

## 📊 Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
See the [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability) for queries and dashboards.


## 📖 System Architecture & Documentation

For details on the overall system design and database implementation, refer to:
* **[System Design Specification](docs/system_design.md)**: Visual diagrams of backend agent flows, approval states, and Firestore JSON schemas.
* **[Database README](app/db/README.md)**: Guide on the local JSON file database and live Google Cloud Firestore configuration.
* **[Frontend Web Portal README](frontend/README.md)**: Details on installing and running the Next.js frontend web app locally.
* **[Agent Evaluation Guide](tests/eval/evalsets/README.md)**: Details the ADK simulation test harness structure, test cases format, and evaluation run parameters.


---

## 🔗 Agent Tools Integration

The Next.js web application interfaces with the custom backend tools configured on the Vertex AI Reasoning Engine agent. The database status changes triggered in the UI align with these tools:

* **Employee Verification**: Binds to `lookup_employee` to pull profile details, cost centers, and department information.
* **Request Validation**: Calls `check_existing_requests` to determine cooldown blocks and detect policy bypasses (e.g., defective or damaged laptops).
* **Entitlement Resolution**: Syncs with `check_policy` evaluations which decide standard vs. premium tiers and approval paths (Auto-approve vs. Manager).
* **Ticket Management**: Invokes `create_ticket`, `approve_request`, and `mark_received` state updates, building a persistent audit trail.


