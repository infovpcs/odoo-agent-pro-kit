#!/usr/bin/env python3
"""Prove every released compatibility component is detected and reversible."""
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    "sandbox/config/artifacts.lock",
    "sandbox/config/images.lock",
    "sandbox/kits/odoo-mixin/spec.yaml",
    "sandbox/schemas/session.schema.json",
    "sandbox/schemas/operation-result.schema.json",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


baseline = {name: digest(ROOT / name) for name in FILES}
with tempfile.TemporaryDirectory(prefix="phase7-upgrade-") as directory:
    stage = Path(directory)
    for name in FILES:
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())

    artifacts = stage / "sandbox/config/artifacts.lock"
    value = json.loads(artifacts.read_text())
    value["agents"]["codex"]["template"] = "candidate:codex"
    value["release"] = "0.5.2-candidate"
    artifacts.write_text(json.dumps(value, indent=2) + "\n")

    kit = stage / "sandbox/kits/odoo-mixin/spec.yaml"
    kit.write_text(kit.read_text().replace("version: 0.5.1", "version: 0.5.2"))

    images = stage / "sandbox/config/images.lock"
    images.write_text(images.read_text().replace("ODOO_19_BASE=", "ODOO_19_CANDIDATE=").replace("POSTGRES_15=", "POSTGRES_15_CANDIDATE="))

    for schema_name in ("session.schema.json", "operation-result.schema.json"):
        schema = stage / "sandbox/schemas" / schema_name
        schema.write_text(schema.read_text().replace('"1.0.0"', '"1.1.0"'))

    changed = [name for name in FILES if digest(stage / name) != baseline[name]]
    assert changed == FILES, changed
    for name in FILES:
        (stage / name).write_bytes((ROOT / name).read_bytes())
    assert {name: digest(stage / name) for name in FILES} == baseline

print("OK: template, kit, Odoo image, Postgres image, and schema upgrade changes were detected and byte-identical rollback passed")
