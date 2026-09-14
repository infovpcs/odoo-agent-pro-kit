#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Fail fast and actionably when a test dependency is absent, instead of letting
# pytest/import errors surface halfway through the suite. The declarations live
# in requirements-dev.txt; tests/test_dev_dependencies.py fails if this list and
# that file drift apart.
echo "==> Python test dependencies"
python3 - <<'PY'
import importlib.util
import sys

# import name -> distribution name, kept in step with requirements-dev.txt.
REQUIRED = {"pytest": "pytest", "yaml": "PyYAML"}
missing = sorted(pkg for module, pkg in REQUIRED.items() if importlib.util.find_spec(module) is None)
if missing:
    sys.exit(
        "FAIL: missing Python test dependency: " + ", ".join(missing)
        + "\n  Install them with: python3 -m pip install -r requirements-dev.txt"
    )
print("OK: " + ", ".join(sorted(REQUIRED.values())) + " present")
PY

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
  integrations/deepseek/install.sh \
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
  plugin/hooks/odoo_hook.py \
  scripts/contributor_hook.py \
  plugin/hooks/checks/__init__.py \
  plugin/hooks/checks/common.py \
  plugin/hooks/checks/version.py \
  plugin/hooks/checks/guard.py \
  plugin/hooks/checks/paths.py \
  plugin/hooks/checks/gates.py \
  plugin/hooks/checks/authz.py \
  plugin/hooks/checks/odoo_lint.py \
  plugin/hooks/checks/sandbox_result.py \
  plugin/hooks/checks/hermes_adapter.py \
  sandbox/bin/sandboxctl \
  sandbox/scripts/fixture-lifecycle.py \
  sandbox/scripts/benchmark.py \
  sandbox/scripts/dependency-inventory.py \
  sandbox/scripts/migrate-local.py \
  sandbox/scripts/release-acceptance.py \
  sandbox/tests/upgrade-rollback.py \
  sandbox/tests/phase6-verify.py

echo "==> Hook smoke test"
for ev in SessionStart UserPromptSubmit PreToolUse PostToolUse Stop SessionEnd; do
  echo '{}' | python3 plugin/hooks/odoo_hook.py "$ev" >/dev/null || {
    echo "FAIL: odoo_hook.py $ev did not exit 0 on empty payload"; exit 1; }
done
for ev in SessionStart PreToolUse Stop; do
  echo '{}' | python3 scripts/contributor_hook.py "$ev" >/dev/null || {
    echo "FAIL: contributor_hook.py $ev did not exit 0 on empty payload"; exit 1; }
done
python3 -c "import json; json.load(open('plugin/hooks/hooks.json')); json.load(open('.claude/settings.json'))"

echo "==> Git whitespace validation"
git diff --check

# Refresh the contributor-hook validate stamp (scripts/contributor_hook.py checks its mtime)
[ -d .git ] && touch .git/odoo-kit-validate.stamp || true

echo "OK: all repository validation checks passed."
