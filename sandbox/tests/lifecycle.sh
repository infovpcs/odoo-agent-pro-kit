#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CTL="$REPO_ROOT/sandbox/bin/sandboxctl"
RUN_ID="${SANDBOX_MATRIX_RUN_ID:-live}"
VERSIONS=(17 18 19)

cd "$REPO_ROOT"

cleanup() {
  local version session
  for version in "${VERSIONS[@]}"; do
    session="${version}-fixture-${RUN_ID}"
    if test -d "$REPO_ROOT/.sandbox/sessions/$session"; then
      "$CTL" destroy "$session" || true
    fi
  done
}
trap cleanup EXIT

pids=()
for version in "${VERSIONS[@]}"; do
  "$CTL" create --version "$version" --module sandbox_fixture --session "${version}-fixture-${RUN_ID}" &
  pids+=("$!")
done
for pid in "${pids[@]}"; do
  wait "$pid"
done

pids=()
for version in "${VERSIONS[@]}"; do
  (
    session="${version}-fixture-${RUN_ID}"
    env_file="$REPO_ROOT/.sandbox/sessions/$session/runtime.env"
    compose=(docker compose --env-file "$env_file" -f "$REPO_ROOT/sandbox/compose/compose.yaml")

    "${compose[@]}" stop odoo
    "${compose[@]}" run --rm odoo odoo --config /etc/odoo/odoo.conf --database sandbox_db --init sandbox_fixture --stop-after-init --no-http
    sed -i.bak 's/>installed</>updated</' "$REPO_ROOT/.sandbox/sessions/$session/addons/sandbox_fixture/data/fixture_data.xml"
    rm "$REPO_ROOT/.sandbox/sessions/$session/addons/sandbox_fixture/data/fixture_data.xml.bak"
    "${compose[@]}" run --rm odoo odoo --config /etc/odoo/odoo.conf --database sandbox_db --update sandbox_fixture --stop-after-init --no-http
    "${compose[@]}" start odoo

    for _ in $(seq 1 60); do
      if "$CTL" exec "$session" -- python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8069/web/health", timeout=2).read()'; then
        break
      fi
      sleep 2
    done
    "$CTL" exec "$session" -- python3 /workspace/scripts/fixture-lifecycle.py
    "$CTL" stop "$session"
    "$CTL" start "$session"
    export_path="$($CTL export "$session")"
    test -s "$export_path"
  ) &
  pids+=("$!")
done
for pid in "${pids[@]}"; do
  wait "$pid"
done

for version in "${VERSIONS[@]}"; do
  session="${version}-fixture-${RUN_ID}"
  "$CTL" destroy "$session"
  test -z "$(docker volume ls --filter "name=^${session}_" --format '{{.Name}}')"
done
trap - EXIT

echo "OK: concurrent Odoo 17/18/19 install, update, protocol CRUD, restart, export, and cleanup passed."
