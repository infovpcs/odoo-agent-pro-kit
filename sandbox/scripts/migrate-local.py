#!/usr/bin/env python3
"""Copy a local custom-addons Git tree into a sandbox import staging area."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True)
parser.add_argument("--version", required=True, choices=["17", "18", "19"])
parser.add_argument("--name", required=True)
parser.add_argument("--output-root", default=".sandbox/imports")
args = parser.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9_]*", args.name):
    raise SystemExit("name must be a valid Odoo technical module name")
source = Path(args.source).resolve()
if not source.is_dir() or not (source / ".git").exists():
    raise SystemExit("source must be the root of a Git repository")
if source == ROOT or ROOT in source.parents:
    raise SystemExit("refusing to import this repository or one of its children")
dirty = subprocess.run(["git", "-C", str(source), "status", "--porcelain"], text=True, capture_output=True, check=True).stdout.strip()
if dirty:
    raise SystemExit("source has uncommitted changes; commit or export a patch first")
output_root = (ROOT / args.output_root).resolve()
target = (output_root / f"{args.version}-{args.name}").resolve()
if output_root not in target.parents:
    raise SystemExit("migration target must remain inside the output root")
if target.exists():
    raise SystemExit(f"target already exists: {target}")
shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git", ".env", "*.conf", "*.log", "__pycache__"))
report = {"schema_version": "1.0.0", "source": str(source), "target": str(target), "odoo_version": args.version, "secrets_copied": False, "next": f"sandbox/bin/sandboxctl create --version {args.version} --module {args.name}"}
(target / "migration-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
