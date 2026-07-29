#!/usr/bin/env bash
# bootstrap.sh — one-command entrypoint for Odoo Agent Pro Kit
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$HOME/odoo-workspaces"
VERSIONS="19"
SKIP_DEPS=0
SKIP_DB=0

usage() {
  cat <<'EOF'
Usage: ./bootstrap.sh [--versions LIST] [--base-dir DIR] [--skip-deps] [--skip-db]

One-command entrypoint: bootstraps local Odoo workspace(s) via
odoo_local_setup/bootstrap_odoo_env.sh, copies context-templates/ into each
new workspace, and prints next steps for installing the agent plugin.

Options:
  --versions LIST     Comma list of Odoo versions to bootstrap: 17,18,19 (default: 19)
  --base-dir DIR      Base directory for workspaces (default: ~/odoo-workspaces)
  --skip-deps         Do not install operating-system dependencies
  --skip-db           Do not create the PostgreSQL role or databases
  -h, --help          Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --versions) VERSIONS="$2"; shift 2 ;;
    --base-dir) BASE_DIR="$2"; shift 2 ;;
    --skip-deps) SKIP_DEPS=1; shift ;;
    --skip-db) SKIP_DB=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

echo "==> Bootstrapping Odoo workspace(s) [$VERSIONS] under $BASE_DIR"
bootstrap_args=(--base-dir "$BASE_DIR" --versions "$VERSIONS")
[ "$SKIP_DEPS" -eq 1 ] && bootstrap_args+=(--skip-deps)
[ "$SKIP_DB" -eq 1 ] && bootstrap_args+=(--skip-db)
"$REPO_ROOT/odoo_local_setup/bootstrap_odoo_env.sh" "${bootstrap_args[@]}"

IFS=',' read -ra VERSION_LIST <<< "$VERSIONS"
for v in "${VERSION_LIST[@]}"; do
  ws="$BASE_DIR/${v}_workspace"
  echo "==> Copying context templates into $ws"
  mkdir -p "$ws/.github"
  cp "$REPO_ROOT/context-templates/AGENTS.md" "$ws/AGENTS.md"
  cp "$REPO_ROOT/context-templates/CLAUDE.md" "$ws/CLAUDE.md"
  cp "$REPO_ROOT/context-templates/GEMINI.md" "$ws/GEMINI.md"
  cp "$REPO_ROOT/context-templates/copilot-instructions.md" "$ws/.github/copilot-instructions.md"
  touch "$ws/.env"
  if grep -q '^export ODOO_AGENT_PRO_KIT_HOME=' "$ws/.env"; then
    sed -i.bak "s|^export ODOO_AGENT_PRO_KIT_HOME=.*|export ODOO_AGENT_PRO_KIT_HOME=\"$REPO_ROOT\"|" "$ws/.env"
    rm -f "$ws/.env.bak"
  else
    printf 'export ODOO_AGENT_PRO_KIT_HOME="%s"\n' "$REPO_ROOT" >> "$ws/.env"
  fi
done

cat <<EOF

Workspace(s) ready under: $BASE_DIR

Next steps:
  1. Install the Claude Code plugin (one time):
       /plugin marketplace add infovpcs/odoo-agent-pro-kit
       /plugin install odoo-agent-pro-kit
  2. For Codex, Cursor, Antigravity, VS Code, or GitHub Copilot: see integrations/<tool>/INSTALL.md
  3. From your agent, run /plan-analysis <version> to begin.
EOF
