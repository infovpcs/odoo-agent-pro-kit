#!/usr/bin/env bash
# SessionStart hook: detect the active Odoo version workspace and print its MCP port.
# No-ops (exit 0, no output) when run outside a recognized Odoo workspace.
set -uo pipefail

VERSION=""
for v in 19.0 18.0 17.0; do
  if [ -d "./$v" ]; then
    VERSION="$v"
    break
  fi
done

if [ -z "$VERSION" ]; then
  exit 0
fi

case "$VERSION" in
  17.0) PORT=8765 ;;
  18.0) PORT=8766 ;;
  19.0) PORT=8767 ;;
esac

echo "[odoo-agent-pro-kit] Detected Odoo $VERSION workspace in $(pwd) — MCP server port $PORT"
exit 0
