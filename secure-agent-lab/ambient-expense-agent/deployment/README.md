# Deployment Guide — Ambient Expense Agent

This document covers the end-to-end process for deploying the agent to
**Vertex AI Agent Runtime** in Google Cloud.

---

## Prerequisites

| Tool | Install |
|------|---------|
| `agents-cli` | `uv tool install google-agents-cli` |
| `terraform` ≥ 1.0 | [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads) |
| `gcloud` CLI | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |

Authenticate once before running any of the steps below:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

---

## Step 1 — Provision Infrastructure (one-time)

The Terraform configuration in `deployment/terraform/single-project/` provisions:

- **Vertex AI Agent Runtime** (`google_vertex_ai_reasoning_engine`) — the managed
  serverless runtime that hosts the agent
- **Service Account** with least-privilege IAM roles
- **GCS bucket** for artifact/log storage
- **Cloud logging sinks** + BigQuery dataset for telemetry
- **Required GCP APIs**

### Option A — via `agents-cli` (recommended)

```bash
# Preview changes first (terraform init + plan)
make infra-plan PROJECT=YOUR_PROJECT_ID

# Apply after reviewing the plan
make infra-apply PROJECT=YOUR_PROJECT_ID
```

### Option B — raw Terraform

```bash
cd deployment/terraform/single-project

# 1. Copy and fill in the tfvars template
cp vars/env.tfvars vars/my.tfvars
# Edit vars/my.tfvars: set project_id and optionally region/project_name

# 2. Initialise Terraform
terraform init

# 3. Preview
terraform plan -var-file=vars/my.tfvars

# 4. Apply
terraform apply -var-file=vars/my.tfvars
```

> [!IMPORTANT]
> Terraform creates the Agent Runtime resource with a **dummy source bundle**.
> The actual agent code is pushed on first `make deploy`. The `lifecycle { ignore_changes }`
> block in `service.tf` prevents Terraform from overwriting subsequent code deployments.

---

## Step 2 — Deploy the Agent

### Quick deploy (uses `agents-cli`)

```bash
# Recommended: run from project root
make deploy PROJECT=YOUR_PROJECT_ID

# With a custom region
make deploy PROJECT=YOUR_PROJECT_ID REGION=us-central1

# Start async and return immediately
make deploy-async PROJECT=YOUR_PROJECT_ID

# Check status of a previous async deploy
make deploy-status
```

### Manual / CI equivalent

```bash
./deployment/deploy.sh --project YOUR_PROJECT_ID --region us-east1
```

Pass `--no-wait` to return immediately and poll later with `agents-cli deploy --status`.

---

## Step 3 — Verify

After a successful deploy the CLI prints an **Agent Runtime resource name**:

```
projects/YOUR_PROJECT_ID/locations/us-east1/reasoningEngines/XXXXXXXXXXXXXXX
```

This value is also stored in `deployment_metadata.json`.

Run a smoke test:

```bash
agents-cli playground   # interactive local test against the deployed instance
```

Or hit the health endpoint directly:

```bash
gcloud ai reasoning-engines describe RESOURCE_NAME --region=us-east1
```

---

## Configuration Reference

### Environment variables injected by Terraform

| Variable | Source | Purpose |
|----------|--------|---------|
| `LOGS_BUCKET_NAME` | Terraform output | GCS bucket for artifact storage |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | `service.tf` | Enable full trace capture |
| `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` | `service.tf` | Enable Agent Runtime telemetry |

### Scaling knobs (edit `service.tf` → `deployment_spec`)

| Variable | Default | Description |
|----------|---------|-------------|
| `min_instances` | 1 | Always-warm containers |
| `max_instances` | 10 | Scale ceiling |
| `container_concurrency` | 9 | Concurrent requests per container |
| `cpu` | 4 | vCPU per container |
| `memory` | 8Gi | RAM per container |

---

## Updating Dependencies

After changing `pyproject.toml` dependencies, regenerate the pinned requirements
file used by Agent Runtime:

```bash
make requirements
```

Then redeploy:

```bash
make deploy PROJECT=YOUR_PROJECT_ID
```

---

## Teardown

```bash
make infra-destroy PROJECT=YOUR_PROJECT_ID
```

> [!CAUTION]
> This permanently deletes the Agent Runtime, GCS bucket, and all IAM bindings
> created by Terraform. It does **not** delete data already written to BigQuery.
