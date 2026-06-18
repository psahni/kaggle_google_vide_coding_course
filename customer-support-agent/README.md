# customer-support-agent

Graph workflow agent for shipping company customer support. Routes customer queries based on topic:
- **Shipping-related** queries (rates, tracking, delivery, returns) → Shipping FAQ agent
- **Unrelated** queries → Polite decline message

Built with **ADK 2.0 Workflows** and **Groq LLM**.

Agent generated with `agents-cli` version `0.5.0`

## Project Structure

```
customer-support-agent/
├── app/
│   ├── agent.py               # Graph workflow definition
│   ├── groq_utils.py          # Groq API integration
│   ├── .env                   # Environment variables (includes GROQ_API_KEY)
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
└── pyproject.toml             # Project dependencies
```

## Graph Workflow

```
START → classify_query → shipping_faq_agent (if shipping-related)
                      → decline_politely (if unrelated)
```

1. **classify_query**: Determines if query is shipping-related
2. **shipping_faq_agent**: Answers shipping questions using Groq LLM
3. **decline_politely**: Returns friendly decline message for non-shipping topics

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com) and add your key to `app/.env`


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

> **Note**: The `agents-cli playground` command has a known issue with argument parsing. Use the workaround below if needed.

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with the playground.

### Testing the Agent

#### Method 1: Direct Python Testing (Quick)

```bash
uv run python3 << 'EOF'
import os
from pathlib import Path

# Load environment
env_file = Path("app/.env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# Test workflow
from app.agent import classify_query, shipping_faq_agent

query = "What are your shipping rates?"
event = classify_query(query)
response = shipping_faq_agent(query)
print(response)
EOF
```

#### Method 2: Web UI Playground (Interactive)

**Issue**: `agents-cli playground` has an argument parsing bug.

**Workaround**:
```bash
uv run adk web --host 127.0.0.1 --port 8080 app
```

Then access the UI at: **`http://127.0.0.1:8080/dev-ui/?app=app`**

**Why the workaround is needed**:
- `agents-cli playground` calls `adk web .` which misinterprets directory contents as arguments
- Error: `Got unexpected extra arguments (app Dockerfile GEMINI.md ...)`
- Direct `adk web app` command works correctly when arguments are in the right order

### Code Quality

Run linting to verify code health:

```bash
agents-cli lint
```

This checks:
- **Ruff**: Import sorting, code style, formatting
- **Codespell**: Spelling errors
- **ty**: Type safety

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Project Files Reference

### `app/agent.py`
The main workflow definition. Defines the graph topology with three nodes:
- `classify_query()`: Classifies queries as shipping-related or unrelated
- `shipping_faq_agent()`: Answers shipping questions using Groq LLM
- `decline_politely()`: Returns polite decline message for out-of-scope queries

### `app/groq_utils.py`
Custom Groq API integration layer. Provides:
- `get_groq_client()`: Initializes Groq client with API key
- `call_groq_model()`: Wrapper for calling Groq models with system prompts and parameters
- Supports configurable models, temperature, and token limits

### `app/app_utils/telemetry.py`
OpenTelemetry configuration for production observability (not active in development):
- Configures prompt/response logging to Google Cloud Storage
- Tracks LLM interactions with metadata (no sensitive content by default)
- Only activates when deployed with `LOGS_BUCKET_NAME` environment variable
- **Current status**: Boilerplate scaffolding (not used locally)

### `app/app_utils/typing.py`
Pydantic data models for type safety and API contracts:
- `Feedback` model: Defines user feedback structure with score, text, user_id, session_id
- Used for validating feedback submissions
- Automatically generates API documentation in FastAPI
- **Current status**: Boilerplate scaffolding (not implemented yet)

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging. When deployed to Google Cloud with proper configuration, the agent automatically logs all interactions for monitoring and debugging.
