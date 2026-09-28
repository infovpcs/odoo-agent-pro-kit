#!/usr/bin/env python3
"""Compare two Odoo backend-test logs by test name (no LLM): baseline (e.g. 19) vs target (e.g. 20).

Exit 0 when no test that passed in the baseline fails, errors, is skipped or is missing in the
target; 1 on any such regression; 2 when a log contains no tests (a vacuous comparison).
Baseline failures may stay failing: a migration keeps pre-existing failures, and fixes are listed.
The JSON result is what a `backend_tests_baseline_parity` record cites.

Usage: test-parity.py BASELINE_LOG TARGET_LOG [--module ADDON ...] [--json FILE]
"""
import argparse
import json
import re
import sys
from pathlib import Path

# "<date> <time> <pid> LEVEL <db> odoo.addons.<addon>.tests.<file>: <message>"
LINE = re.compile(r"^\S+ \S+ \d+ (?P<level>[A-Z]+) \S+ odoo\.addons\.(?P<addon>\w+)\.tests\.(?P<file>[\w.]+): (?P<message>.*?)\s*$")
STARTING = re.compile(r"Starting (?P<test>.+?) \.\.\.$")
OUTCOME = re.compile(r"(?P<flavour>FAIL|ERROR): (?P<test>.+)$")
SKIPPED = re.compile(r"skipped (?P<test>.+?) : ")
# Class-level failures are logged by the suite, not the addon: "ERROR: setUpClass (odoo.addons.<addon>.tests.<file>.<Class>)".
CLASS_ERROR = re.compile(r"^\S+ \S+ \d+ ERROR \S+ odoo\.tests\.\w+: (?:FAIL|ERROR): (?P<test>\w+ \(odoo\.addons\.(?P<addon>\w+)\.tests\.(?P<file>\w+)\.\w+\))\s*$")
RANK = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
STATUSES = ("passed", "failed", "error", "skipped")


def parse_log(text):
    """Return {"addon/file:Class.test": status}; a test logged twice keeps its worst status."""
    results = {}

    def record(key, status):
        if RANK[status] >= RANK.get(results.get(key, ""), -1):
            results[key] = status

    for raw in text.splitlines():
        if class_error := CLASS_ERROR.match(raw):
            record(f"{class_error['addon']}/{class_error['file']}:{class_error['test']}", "error")
            continue
        match = LINE.match(raw)
        if not match:
            continue
        prefix = f"{match['addon']}/{match['file']}:"
        message = match["message"]
        if started := STARTING.fullmatch(message):
            results.setdefault(prefix + started["test"], "passed")
        elif (outcome := OUTCOME.fullmatch(message)) and match["level"] == "ERROR":
            record(prefix + outcome["test"], "failed" if outcome["flavour"] == "FAIL" else "error")
        elif skipped := SKIPPED.match(message):
            record(prefix + skipped["test"], "skipped")
    return results


def summary(results):
    counts = {status: sum(1 for value in results.values() if value == status) for status in STATUSES}
    counts["total"] = len(results)
    return counts


def compare(baseline, target, modules=None):
    if modules:
        wanted = set(modules)
        baseline = {k: v for k, v in baseline.items() if k.split("/", 1)[0] in wanted}
        target = {k: v for k, v in target.items() if k.split("/", 1)[0] in wanted}
    regressions, improvements, new = [], [], []
    for test in sorted(baseline):
        before, after = baseline[test], target.get(test, "missing")
        if before == "passed" and after != "passed":
            regressions.append({"test": test, "baseline": before, "target": after})
        elif before != "passed" and after == "passed":
            improvements.append({"test": test, "baseline": before, "target": after})
    for test in sorted(set(target) - set(baseline)):
        new.append({"test": test, "target": target[test]})
    return {
        "parity": not regressions,
        "summary": {"baseline": summary(baseline), "target": summary(target)},
        "regressions": regressions, "improvements": improvements, "new": new,
        "tests": [{"test": t, "baseline": baseline.get(t, "missing"), "target": target.get(t, "missing")}
                  for t in sorted(set(baseline) | set(target))],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baseline_log"); parser.add_argument("target_log")
    parser.add_argument("--module", action="append", help="limit to this addon (repeatable)")
    parser.add_argument("--json", metavar="FILE", help="write the full result here")
    args = parser.parse_args(argv)
    baseline = parse_log(Path(args.baseline_log).read_text(errors="replace"))
    target = parse_log(Path(args.target_log).read_text(errors="replace"))
    for name, results in (("baseline", baseline), ("target", target)):
        if not results:
            print(f"test-parity: no tests found in the {name} log; refusing a vacuous comparison", file=sys.stderr)
            return 2
    report = {"schema_version": "1.0.0", "baseline_log": str(Path(args.baseline_log).resolve()),
              "target_log": str(Path(args.target_log).resolve()), "modules": args.module or [],
              **compare(baseline, target, args.module)}
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n")
    b, t = report["summary"]["baseline"], report["summary"]["target"]
    print(f"baseline: {b['passed']} passed, {b['failed']} failed, {b['error']} error, {b['skipped']} skipped of {b['total']}")
    print(f"target:   {t['passed']} passed, {t['failed']} failed, {t['error']} error, {t['skipped']} skipped of {t['total']}")
    for item in report["regressions"]:
        print(f"REGRESSION {item['test']}: {item['baseline']} -> {item['target']}")
    for item in report["improvements"]:
        print(f"fixed      {item['test']}: {item['baseline']} -> {item['target']}")
    print("parity: " + ("PASS" if report["parity"] else "FAIL"))
    return 0 if report["parity"] else 1


if __name__ == "__main__":
    sys.exit(main())
