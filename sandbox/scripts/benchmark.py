#!/usr/bin/env python3
"""Record reproducible controller timing/resource samples as JSONL."""
import argparse
import datetime as dt
import json
import platform
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--label", required=True, choices=["cold", "warm", "recovery", "six-session"])
parser.add_argument("--output", default=".sandbox/release/benchmarks.jsonl")
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
if not args.command:
    raise SystemExit("provide a command after --")
command = args.command[1:] if args.command[0] == "--" else args.command
started = time.monotonic()
proc = subprocess.run(command, cwd=ROOT, check=False)
record = {
    "schema_version": "1.0.0", "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    "label": args.label, "duration_seconds": round(time.monotonic() - started, 3),
    "exit_code": proc.returncode, "platform": platform.platform(), "command": command,
}
target = ROOT / args.output
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("a") as stream:
    stream.write(json.dumps(record, sort_keys=True) + "\n")
raise SystemExit(proc.returncode)
