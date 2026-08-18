#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "==> Repository tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests

echo "==> Skill validation"
python3 scripts/validate_skills.py plugin/skills

echo "==> Docker Sandbox artifact validation"
sandbox/scripts/validate-artifacts.sh
python3 sandbox/scripts/release-acceptance.py verify
python3 sandbox/tests/upgrade-rollback.py

echo "==> Compose validation"
if command -v docker >/dev/null 2>&1; then
  sandbox/scripts/validate-compose.sh
else
  echo "SKIP: Docker CLI unavailable"
fi

echo "==> Shell syntax"
bash -n \
  bootstrap.sh \
  odoo_local_setup/*.sh \
  plugin/hooks/*.sh \
  plugin/odoo_mcp/*.sh \
  sandbox/bin/sandbox-agent \
  sandbox/scripts/*.sh \
  sandbox/tests/*.sh \
  scripts/validate.sh

echo "==> Python syntax"
python3 -m py_compile \
  plugin/__init__.py \
  sandbox/bin/sandboxctl \
  sandbox/scripts/fixture-lifecycle.py \
  sandbox/scripts/benchmark.py \
  sandbox/scripts/dependency-inventory.py \
  sandbox/scripts/migrate-local.py \
  sandbox/scripts/release-acceptance.py \
  sandbox/tests/upgrade-rollback.py \
  sandbox/tests/phase6-verify.py

echo "==> Git whitespace validation"
git diff --check

echo "OK: all repository validation checks passed."
