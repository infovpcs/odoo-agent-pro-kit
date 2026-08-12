#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CTL="$REPO_ROOT/sandbox/bin/sandboxctl"
RUNS="${SANDBOX_LIFECYCLE_RUNS:-4}"

cd "$REPO_ROOT"

for attempt in $(seq 1 "$RUNS"); do
  session="19-fixture-live-${attempt}"
  "$CTL" create --version 19 --module sandbox_fixture --session "$session"
  env_file="$REPO_ROOT/.sandbox/sessions/$session/runtime.env"
  compose=(docker compose --env-file "$env_file" -f "$REPO_ROOT/sandbox/compose/compose.yaml")

  "${compose[@]}" stop odoo
  "${compose[@]}" run --rm odoo odoo --config /etc/odoo/odoo.conf --database sandbox_db --init sandbox_fixture --stop-after-init
  "${compose[@]}" run --rm odoo odoo --config /etc/odoo/odoo.conf --database sandbox_db --update sandbox_fixture --stop-after-init
  "${compose[@]}" start odoo

  for _ in $(seq 1 60); do
    if "$CTL" exec "$session" -- python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8069/web/health", timeout=2).read()'; then
      break
    fi
    sleep 2
  done
  "$CTL" exec "$session" -- python3 -c 'import json,urllib.request; request=urllib.request.Request("http://127.0.0.1:8069/web/webclient/version_info", data=json.dumps({"jsonrpc":"2.0","method":"call","params":{},"id":1}).encode(), headers={"Content-Type":"application/json"}); response=json.load(urllib.request.urlopen(request, timeout=5)); assert response["result"]["server_version"].startswith("19.")'
  "$CTL" stop "$session"
  "$CTL" start "$session"
  export_path="$($CTL export "$session")"
  test -s "$export_path"
  "$CTL" destroy "$session"
  test -z "$(docker volume ls --filter "name=^${session}_" --format '{{.Name}}')"
done

echo "OK: $RUNS Odoo 19 fixture lifecycle runs passed (runs 1-2 cold, 3-4 warm)."
