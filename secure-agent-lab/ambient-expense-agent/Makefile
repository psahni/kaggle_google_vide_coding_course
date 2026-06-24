.PHONY: install playground ambient stop stop-ambient stop-playground generate-traces grade \
        requirements deploy deploy-async deploy-status deploy-dry-run \
        infra-plan infra-apply infra-destroy

# ── Local dev ─────────────────────────────────────────────────────────────────
install:
	uv sync

playground:
	uv run adk web expense_agent --host 127.0.0.1 --port 8000 --reload_agents

ambient:
	uv run uvicorn app.main:app --host 127.0.0.1 --port 8080

stop: stop-ambient stop-playground

stop-ambient:
	powershell -Command 'Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $$_ -Force }'

stop-playground:
	powershell -Command 'Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $$_ -Force }'

# ── Evaluation ────────────────────────────────────────────────────────────────
generate-traces:
	python -m tests.eval.generate_traces

grade:
	agents-cli eval grade --config tests/eval/eval_config.yaml --traces ../artifacts/traces/generated_traces.json

# ── Dependency pinning ────────────────────────────────────────────────────────
# Regenerate app/app_utils/.requirements.txt from the lock file.
# Run this after any change to pyproject.toml dependencies, then redeploy.
requirements:
	uv export --no-dev --no-hashes --no-sources --no-header --no-emit-project --locked --no-annotate \
		| grep -v "^hf-xet" \
		> app/app_utils/.requirements.txt
	@echo "✅ app/app_utils/.requirements.txt updated (hf-xet excluded — no Linux/py312 wheel)"

# ── Production deployment (Vertex AI Agent Runtime) ───────────────────────────
# Usage:
#   make deploy PROJECT=my-gcp-project
#   make deploy PROJECT=my-gcp-project REGION=us-central1
PROJECT ?=
REGION  ?= us-east1

deploy: _require-project
	agents-cli deploy \
		--deployment-target agent_runtime \
		--project $(PROJECT) \
		--region  $(REGION) \
		--no-confirm-project

deploy-async: _require-project
	agents-cli deploy \
		--deployment-target agent_runtime \
		--project $(PROJECT) \
		--region  $(REGION) \
		--no-confirm-project \
		--no-wait

deploy-status:
	agents-cli deploy --status

deploy-dry-run: _require-project
	agents-cli deploy \
		--deployment-target agent_runtime \
		--project $(PROJECT) \
		--region  $(REGION) \
		--no-confirm-project \
		--dry-run

# ── Infrastructure (Terraform) ────────────────────────────────────────────────
# Usage:
#   make infra-plan  PROJECT=my-gcp-project
#   make infra-apply PROJECT=my-gcp-project
# These targets run terraform init + plan/apply inside the single-project module.

TFVARS_FILE ?= deployment/terraform/single-project/vars/env.tfvars
TFDIR       := deployment/terraform/single-project

infra-plan: _require-project
	agents-cli infra single-project --project $(PROJECT)

infra-apply: _require-project
	agents-cli infra single-project --project $(PROJECT) --apply

infra-destroy: _require-project
	@echo "⚠️  WARNING: This will destroy all infrastructure for project $(PROJECT)."
	@read -p "Type 'yes' to confirm: " CONFIRM && [ "$$CONFIRM" = "yes" ]
	cd $(TFDIR) && terraform destroy \
		-var="project_id=$(PROJECT)" \
		-var="region=$(REGION)"

# ── Internal helpers ──────────────────────────────────────────────────────────
_require-project:
	@test -n "$(PROJECT)" || (echo "ERROR: PROJECT is required. Run: make <target> PROJECT=your-gcp-project-id" && exit 1)
