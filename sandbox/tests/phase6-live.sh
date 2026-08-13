#!/usr/bin/env bash
set -euo pipefail

session="${1:-phase6-primary}"
module="${2:-sandbox_fixture}"
ctl="sandbox/bin/sandboxctl"
state=".sandbox/sessions/$session"

healthy() {
  "$ctl" status "$session" | python3 -c 'import json,sys; value=json.load(sys.stdin); assert value["status"] in {"ready", "recoverable"}; assert all(row.get("Health") == "healthy" for row in value["services"])'
}

bundle() {
  "$ctl" diagnose "$session" --reason "$1" "${@:2}"
}

"$ctl" module "$session" install "$module"
"$ctl" module "$session" test "$module"
test -s "$state/tests/junit/junit.xml"
test -s "$state/tests/coverage/coverage.xml"
test -s "$state/tests/browser/result.json"

backup="$($ctl backup "$session" | tail -1)"
test -s "$backup"
"$ctl" restore "$session" "$backup"
healthy

docker compose --env-file "$state/runtime.env" -f sandbox/compose/compose.yaml kill -s KILL odoo
bundle odoo-crash >/dev/null
"$ctl" recover "$session" --timeout 180
healthy

docker compose --env-file "$state/runtime.env" -f sandbox/compose/compose.yaml kill -s KILL db
bundle postgres-crash >/dev/null
"$ctl" recover "$session" --timeout 180
healthy

set +e
"$ctl" module "$session" install definitely_invalid_phase6_module
invalid_rc=$?
set -e
test "$invalid_rc" -ne 0
grep -q '"status": "recoverable"' "$state/session.json"
"$ctl" recover "$session" --timeout 180
healthy

set +e
timeout -s INT 1 "$ctl" module "$session" update "$module"
interrupt_rc=$?
set -e
if test "$interrupt_rc" -ne 0; then
  bundle interrupted-operation >/dev/null
  "$ctl" recover "$session" --timeout 180
fi
healthy

pressure="$state/diagnostics/disk-pressure.bin"
dd if=/dev/zero of="$pressure" bs=1M count=128 status=none
bundle disk-pressure >/dev/null
rm "$pressure"
healthy

bundle controller-restart >/dev/null
"$ctl" recover "$session" --timeout 180
healthy

python3 - "$state/diagnostics" "$state/runtime.env" <<'PY'
import pathlib, sys, tarfile

bundles = list(pathlib.Path(sys.argv[1]).glob("*.tar.gz"))
assert len(bundles) >= 6, len(bundles)
secrets = []
for line in pathlib.Path(sys.argv[2]).read_text().splitlines():
    key, _, value = line.partition("=")
    if any(word in key.lower() for word in ("password", "secret", "token", "api_key")) and value:
        secrets.append(value.encode())
for bundle in bundles:
    with tarfile.open(bundle) as archive:
        content = b"".join(archive.extractfile(item).read() for item in archive if item.isfile())
    assert all(secret not in content for secret in secrets), bundle
print(f"PHASE6_BUNDLES={len(bundles)} REDACTION=passed")
PY

echo "PHASE6_PRIMARY=passed"
