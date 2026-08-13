#!/usr/bin/env python3
"""Verify pinned release contracts and record upgrade/rollback decisions."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "sandbox/config"


def semver(value):
    return tuple(int(part) for part in value.split("."))


def load():
    artifacts = json.loads((CONFIG / "artifacts.lock").read_text())
    versions = json.loads((CONFIG / "versions.yaml").read_text())
    images = dict(line.split("=", 1) for line in (CONFIG / "images.lock").read_text().splitlines() if line and not line.startswith("#"))
    return artifacts, versions, images


def verify():
    artifacts, versions, images = load()
    errors = []
    for major, config in versions.items():
        for key in (config["base_image_lock"], config["postgres_image_lock"]):
            value = images.get(key, "")
            if not re.fullmatch(r"[^\s]+@sha256:[0-9a-f]{64}", value):
                errors.append(f"{major}: {key} is not digest pinned")
    kit = artifacts["kits"]["odoo-mixin"]
    digest = hashlib.sha256((ROOT / kit["path"] / "spec.yaml").read_bytes()).hexdigest()
    if digest != kit["spec_sha256"]:
        errors.append("odoo-mixin digest differs from artifacts.lock")
    if artifacts["schema_version"] != "1.0.0":
        errors.append("unsupported artifact schema")
    if errors:
        raise SystemExit("\n".join(errors))
    print("OK: template, kit, image, Postgres, and schema release contracts are pinned")


def compare(previous):
    current, versions, images = load()
    old = json.loads(Path(previous).read_text())
    changes = []
    for key in ("schema_version", "sbx_version", "release"):
        if old.get(key) != current.get(key):
            changes.append({"component": key, "from": old.get(key), "to": current.get(key)})
    if semver(current["schema_version"]) < semver(old.get("schema_version", "0.0.0")):
        raise SystemExit("schema rollback requires an explicit compatible migration")
    print(json.dumps({"compatible": True, "changes": changes, "rollback": "restore previous lock files; never downgrade persisted data without a tested restore"}, indent=2))


parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("verify")
comparison = sub.add_parser("compare")
comparison.add_argument("previous")
args = parser.parse_args()
verify() if args.command == "verify" else compare(args.previous)
