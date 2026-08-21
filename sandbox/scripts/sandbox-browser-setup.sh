#!/usr/bin/env bash
# sandbox-browser-setup.sh — provision the agent-browser CLI inside a Docker
# Sandbox so frontend verification runs next to the sandboxed Odoo instance
# (no SSH tunnels, port publishing, or host relays required).
#
# Usage (from OUTSIDE the sandbox, via sbx exec):
#   sbx exec <sandbox> -- bash /home/ubuntu/workspace/odoo-agent-pro-kit/sandbox/scripts/sandbox-browser-setup.sh
#
# What it does:
#   1. Installs the Vercel agent-browser npm CLI globally.
#   2. Downloads its managed Chromium build plus system dependencies.
#   3. Installs ffmpeg so `agent-browser record` can encode .webm videos.
#   4. Verifies the toolchain end-to-end.
#
# Idempotent: safe to re-run; each step is skipped when already satisfied.
set -euo pipefail

echo "== sandbox browser setup =="

# 1. agent-browser CLI
if command -v agent-browser >/dev/null 2>&1; then
    echo "cli: $(agent-browser --version 2>/dev/null || echo present)"
else
    npm install -g agent-browser >/dev/null
    echo "cli: installed $(agent-browser --version)"
fi

# 2/3. Chromium + system deps (also pulls libraries Chrome needs at runtime)
if [ ! -d "$HOME/.agent-browser/browsers" ] || \
   [ -z "$(ls -A "$HOME/.agent-browser/browsers" 2>/dev/null)" ]; then
    agent-browser install --with-deps
else
    echo "chromium: cached"
fi

# ffmpeg for `agent-browser record start/stop`
if ! command -v ffmpeg >/dev/null 2>&1; then
    SUDO=""
    [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq ffmpeg >/dev/null
fi
echo "ffmpeg: $(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')"

# 4. Verify
agent-browser --version
echo "setup: OK"
