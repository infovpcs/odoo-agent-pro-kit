#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCK_FILE="$REPO_ROOT/sandbox/config/artifacts.lock"
KIT_DIR="$REPO_ROOT/sandbox/kits/odoo-mixin"

python3 - "$LOCK_FILE" "$KIT_DIR/spec.yaml" <<'PY'
import hashlib
import json
import pathlib
import sys

lock_path = pathlib.Path(sys.argv[1])
spec_path = pathlib.Path(sys.argv[2])
lock = json.loads(lock_path.read_text())
kit = lock["kits"]["odoo-mixin"]
digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
assert lock["sbx_version"] == "0.38.x"
assert lock["release"] == kit["version"]
assert f"version: {kit['version']}" in spec_path.read_text()
assert digest == kit["spec_sha256"], f"kit digest mismatch: {digest}"
assert set(lock["agents"]) == {"codex", "claude", "copilot"}
assert all(not item["custom_template_required"] for item in lock["agents"].values())
PY

if command -v sbx >/dev/null 2>&1; then
  case "$(sbx version 2>&1)" in
    *"v0.38."*) ;;
    *) echo "ERROR: Phase 4 supports sbx 0.38.x only" >&2; exit 1 ;;
  esac
  sbx kit validate "$KIT_DIR"
  package_dir="$(mktemp -d "${TMPDIR:-/tmp}/odoo-kit-package.XXXXXX")"
  trap 'rm -rf "$package_dir"' EXIT
  sbx kit pack "$KIT_DIR" --output "$package_dir/odoo-mixin-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["release"])' "$LOCK_FILE").zip"
  test -s "$package_dir"/*.zip
else
  echo "SKIP: sbx is unavailable; run kit validation on the Ubuntu KVM host"
fi

echo "OK: Sandbox artifacts are pinned and structurally valid."
