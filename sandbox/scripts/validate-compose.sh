#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_PROJECT_NAME=validation \
REPOSITORY_ROOT="$ROOT" \
ODOO_BASE_IMAGE="odoo:19.0" \
ODOO_DOCKERFILE="sandbox/images/odoo-dev/19.Dockerfile" \
ODOO_DEV_IMAGE="odoo-agent-dev:validation" \
POSTGRES_IMAGE="postgres:15-bookworm" \
POSTGRES_USER=validation \
POSTGRES_PASSWORD=validation-not-a-secret \
ODOO_DB_NAME=validation \
ODOO_CONFIG_FILE="$ROOT/sandbox/config/odoo.conf.template" \
ADDONS_DIR="$ROOT/sandbox/fixtures" \
SESSION_LOGS_DIR="$ROOT/.sandbox/validation/logs" \
SESSION_RESULTS_DIR="$ROOT/.sandbox/validation/results" \
ODOO_API_PASSWORD=validation-not-a-secret \
ODOO_RPC_PROTOCOL=json2 \
docker compose -f "$ROOT/sandbox/compose/compose.yaml" config --quiet
