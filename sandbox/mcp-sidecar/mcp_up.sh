#!/bin/bash
# Bring up the odoo_mcp sidecar as a Compose service inside an existing
# Docker Sandbox session's stack, then report the (host-loopback) URL.
#
# Usage: mcp_up.sh <session-id> [mcp-port]
#
# Must be run via `sbx exec <sandbox-name> -- bash .../mcp_up.sh <session-id>`
# from INSIDE the sbx microVM that owns the session (it needs that VM's
# private Docker daemon and Compose network) -- NOT on the bare host, and
# NOT before `sandboxctl create` has produced a ready session.
#
# After it returns, publish the port to the sbx host from OUTSIDE the VM:
#   sbx ports <sandbox-name> --publish <mcp-port>:<mcp-port>
#
# Known pitfall: sbx microVMs auto-suspend when idle and cold-reboot on the
# next `sbx exec`. A container started with a bare `docker run` (not part of
# the Compose project) does NOT come back after that reboot and exits
# nonzero. This script avoids that by registering `mcp` as a normal
# `restart: unless-stopped` Compose service in the SAME project as `db`/
# `odoo`, so it restarts exactly like they do.
set -e
SESSION="$1"
MCP_PORT="${2:-}"
if [ -z "$SESSION" ]; then
  echo "usage: $0 <session-id> [mcp-port]" >&2
  exit 1
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="$ROOT/compose/compose.yaml"
OVERRIDE="$ROOT/mcp-sidecar/mcp.override.yaml"
SESSION_DIR="$ROOT/../.sandbox/sessions/$SESSION"
ENVFILE="$SESSION_DIR/runtime.env"

if [ ! -f "$ENVFILE" ]; then
  echo "unknown session: $SESSION (no $ENVFILE)" >&2
  exit 1
fi

VERSION_SERIES=$(python3 -c "import json; print(json.load(open('$SESSION_DIR/session.json'))['odoo_version'])")

# Default MCP port follows the repo's fixed per-version convention:
# 17.0 -> 8765, 18.0 -> 8766, 19.0 -> 8767 (see plugin/odoo_mcp/start_mcp_server.sh)
if [ -z "$MCP_PORT" ]; then
  case "$VERSION_SERIES" in
    17.0) MCP_PORT=8765 ;;
    18.0) MCP_PORT=8766 ;;
    *)    MCP_PORT=8767 ;;
  esac
fi

MCP_ODOO_VERSION="$VERSION_SERIES" MCP_PORT="$MCP_PORT" \
docker compose --env-file "$ENVFILE" -f "$COMPOSE" -f "$OVERRIDE" up -d --build mcp

sleep 3
docker compose --env-file "$ENVFILE" -f "$COMPOSE" -f "$OVERRIDE" ps mcp
docker compose --env-file "$ENVFILE" -f "$COMPOSE" -f "$OVERRIDE" logs --tail 20 mcp

echo ""
echo "MCP sidecar is up inside the sandbox on port ${MCP_PORT}."
echo "Next step (run OUTSIDE the microVM, on the sbx host):"
echo "  sbx ports <sandbox-name> --publish ${MCP_PORT}:${MCP_PORT}"
