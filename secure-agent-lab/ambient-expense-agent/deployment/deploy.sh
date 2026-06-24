#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ---------------------------------------------------------------------------
# deploy.sh — Production deployment script for Vertex AI Agent Runtime
#
# Usage:
#   ./deployment/deploy.sh [OPTIONS]
#
# Options:
#   --project   GCP project ID            (required, or set GCP_PROJECT env var)
#   --region    GCP region                (default: us-east1)
#   --sa        Service account email     (optional; uses default compute SA otherwise)
#   --no-wait   Return immediately after submitting deployment
#   --dry-run   Print the deploy command without executing it
#   --help      Show this help text
#
# Examples:
#   ./deployment/deploy.sh --project my-gcp-project
#   ./deployment/deploy.sh --project my-gcp-project --region us-central1 --no-wait
#   GCP_PROJECT=my-gcp-project ./deployment/deploy.sh --dry-run
# ---------------------------------------------------------------------------

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
PROJECT="${GCP_PROJECT:-}"
REGION="us-east1"
SERVICE_ACCOUNT=""
NO_WAIT=false
DRY_RUN=false

# ── Argument parsing ─────────────────────────────────────────────────────────
usage() {
  grep '^# ' "$0" | sed 's/^# //'
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)  PROJECT="$2";          shift 2 ;;
    --region)   REGION="$2";           shift 2 ;;
    --sa)       SERVICE_ACCOUNT="$2";  shift 2 ;;
    --no-wait)  NO_WAIT=true;          shift   ;;
    --dry-run)  DRY_RUN=true;          shift   ;;
    --help|-h)  usage ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Validation ───────────────────────────────────────────────────────────────
if [[ -z "$PROJECT" ]]; then
  echo "ERROR: --project is required (or set the GCP_PROJECT environment variable)" >&2
  exit 1
fi

# Verify agents-cli is installed
if ! command -v agents-cli &>/dev/null; then
  echo "ERROR: agents-cli not found. Install it with: uv tool install google-agents-cli" >&2
  exit 1
fi

# Verify we are in the project root (agents-cli-manifest.yaml must exist)
if [[ ! -f "agents-cli-manifest.yaml" ]]; then
  echo "ERROR: agents-cli-manifest.yaml not found. Run this script from the project root." >&2
  exit 1
fi

# Verify pinned requirements are present (needed for Agent Runtime packaging)
REQUIREMENTS="app/app_utils/.requirements.txt"
if [[ ! -f "$REQUIREMENTS" ]]; then
  echo "ERROR: $REQUIREMENTS not found. Regenerate with: make requirements" >&2
  exit 1
fi

# ── Build command ────────────────────────────────────────────────────────────
CMD=(
  agents-cli deploy
  --deployment-target agent_runtime
  --project  "$PROJECT"
  --region   "$REGION"
  --no-confirm-project
)

[[ -n "$SERVICE_ACCOUNT" ]] && CMD+=(--service-account "$SERVICE_ACCOUNT")
[[ "$NO_WAIT" == "true"   ]] && CMD+=(--no-wait)

# ── Execute ──────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Ambient Expense Agent — Production Deploy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Project : $PROJECT"
echo "  Region  : $REGION"
echo "  Target  : agent_runtime"
[[ -n "$SERVICE_ACCOUNT" ]] && echo "  SA      : $SERVICE_ACCOUNT"
[[ "$NO_WAIT" == "true"  ]] && echo "  Mode    : async (--no-wait)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY RUN] Would execute:"
  echo "  ${CMD[*]}"
  exit 0
fi

"${CMD[@]}"
