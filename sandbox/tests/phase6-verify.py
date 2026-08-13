#!/usr/bin/env python3
"""Verify Phase 6 live evidence without printing runtime secrets."""

import json
import sys
import tarfile
from pathlib import Path


session = sys.argv[1] if len(sys.argv) > 1 else "phase6-primary"
state = Path(".sandbox/sessions") / session
required_reasons = {
    "odoo-crash", "postgres-crash", "invalid-module", "interrupted-operation",
    "disk-pressure", "controller-restart", "denied-network", "telemetry-proof",
}
required_files = {
    "bundle.json", "compose-state.json", "compose-processes.log", "resources.jsonl",
    "service-logs.log", "policy.json", "session.json", "events.jsonl",
}
secrets = []
for line in (state / "runtime.env").read_text().splitlines():
    key, _, value = line.partition("=")
    if any(word in key.lower() for word in ("password", "secret", "token", "api_key")) and value:
        secrets.append(value.encode())

reasons = set()
for bundle in (state / "diagnostics").glob("*.tar.gz"):
    with tarfile.open(bundle) as archive:
        names = set(archive.getnames())
        assert required_files <= names, (bundle, required_files - names)
        metadata = json.load(archive.extractfile("bundle.json"))
        reasons.add(metadata["reason"])
        content = b"".join(archive.extractfile(item).read() for item in archive if item.isfile())
    assert all(secret not in content for secret in secrets), bundle

assert required_reasons <= reasons, required_reasons - reasons
assert json.loads((state / "session.json").read_text())["status"] == "ready"
print(f"BUNDLES={len(list((state / 'diagnostics').glob('*.tar.gz')))} REDACTION=passed REASONS=passed")
