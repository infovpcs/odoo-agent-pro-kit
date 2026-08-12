#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "==> Repository tests"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests

echo "==> Skill validation"
python3 scripts/validate_skills.py plugin/skills

echo "==> Shell syntax"
bash -n \
  bootstrap.sh \
  odoo_local_setup/*.sh \
  plugin/hooks/*.sh \
  plugin/odoo_mcp/*.sh \
  sandbox/scripts/*.sh \
  sandbox/tests/*.sh \
  scripts/validate.sh

echo "==> Python syntax"
python3 -m py_compile sandbox/bin/sandboxctl

echo "==> Git whitespace validation"
git diff --check

echo "OK: all repository validation checks passed."
