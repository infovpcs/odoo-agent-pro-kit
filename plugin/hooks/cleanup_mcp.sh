#!/usr/bin/env bash
# Stop hook: gracefully terminate any MCP server processes started this session.
# No-ops if the plugin's odoo_mcp/ directory or its pid files aren't present.
set -uo pipefail

PID_DIR="${CLAUDE_PLUGIN_ROOT:-.}/odoo_mcp"

if [ ! -d "$PID_DIR" ]; then
  exit 0
fi

for pid_file in "$PID_DIR"/mcp_server_*.pid; do
  [ -e "$pid_file" ] || continue
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "[odoo-agent-pro-kit] Stopped MCP server pid $pid"
  fi
  rm -f "$pid_file"
done
exit 0
