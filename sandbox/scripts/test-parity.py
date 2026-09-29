#!/usr/bin/env python3
"""Compare two Odoo backend-test logs by test name (no LLM): baseline (e.g. 19) vs target (e.g. 20).

Exit 0 when no test that passed in the baseline fails, errors, is skipped or is missing in the
target; 1 on any such regression; 2 when a log contains no tests (a vacuous comparison) or the
arguments are malformed. Baseline failures may stay failing: a migration keeps pre-existing
failures, and fixes are listed. The JSON result is what a `backend_tests_baseline_parity` record cites.

Parity alone is not the pass criterion for a migration (Phase 11 finding 3): a module that fails
to install but had no passing test on the baseline never shows up as a regression. With
`--expect-module` (the modules that must be migrated) and `--install-exit MODULE=CODE` (the
install exit code recorded per module) the check also fails when an expected module did not
install, has no recorded install, or has no test result on the target where the baseline had one.

Usage: test-parity.py BASELINE_LOG TARGET_LOG [--module ADDON ...] [--expect-module ADDON ...]
                      [--install-exit ADDON=CODE ...] [--json FILE]
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


def module_check(baseline, target, expected, install_exits):
    """Per expected module: installed (exit 0), and tested on the target when the baseline had tests."""
    modules = []
    for module in expected:
        before = sum(1 for key in baseline if key.split("/", 1)[0] == module)
        after = sum(1 for key in target if key.split("/", 1)[0] == module)
        code = install_exits.get(module)
        reason = None
        if code is None:
            reason = "install exit code not recorded"
        elif code != 0:
            reason = f"install failed (exit {code})"
        elif before and not after:
            reason = f"no test result on the target ({before} on the baseline)"
        modules.append({"module": module, "install_exit": code, "baseline_tests": before, "target_tests": after,
                        "ok": reason is None, "reason": reason})
    return {"ok": all(m["ok"] for m in modules), "modules": modules}


def install_exit(value):
    module, _, code = value.partition("=")
    if not module or not code.lstrip("-").isdigit():
        raise argparse.ArgumentTypeError(f"--install-exit expects MODULE=CODE, got {value!r}")
    return module, int(code)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baseline_log"); parser.add_argument("target_log")
    parser.add_argument("--module", action="append", help="limit to this addon (repeatable)")
    parser.add_argument("--expect-module", action="append", default=[], help="a module that must install and keep its tests (repeatable)")
    parser.add_argument("--install-exit", action="append", default=[], type=install_exit, metavar="ADDON=CODE",
                        help="install exit code recorded for a module (repeatable)")
    parser.add_argument("--json", metavar="FILE", help="write the full result here")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return exit_.code
    baseline = parse_log(Path(args.baseline_log).read_text(errors="replace"))
    target = parse_log(Path(args.target_log).read_text(errors="replace"))
    for name, results in (("baseline", baseline), ("target", target)):
        if not results:
            print(f"test-parity: no tests found in the {name} log; refusing a vacuous comparison", file=sys.stderr)
            return 2
    report = {"schema_version": "1.1.0", "baseline_log": str(Path(args.baseline_log).resolve()),
              "target_log": str(Path(args.target_log).resolve()), "module_filter": args.module or [],
              **compare(baseline, target, args.module)}
    check = module_check(baseline, target, args.expect_module, dict(args.install_exit))
    report["modules"] = check["modules"]
    report["pass"] = report["parity"] and check["ok"]
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n")
    b, t = report["summary"]["baseline"], report["summary"]["target"]
    print(f"baseline: {b['passed']} passed, {b['failed']} failed, {b['error']} error, {b['skipped']} skipped of {b['total']}")
    print(f"target:   {t['passed']} passed, {t['failed']} failed, {t['error']} error, {t['skipped']} skipped of {t['total']}")
    for item in report["regressions"]:
        print(f"REGRESSION {item['test']}: {item['baseline']} -> {item['target']}")
    for item in report["improvements"]:
        print(f"fixed      {item['test']}: {item['baseline']} -> {item['target']}")
    for item in report["modules"]:
        print(f"module     {item['module']}: install exit {item['install_exit']}, tests {item['baseline_tests']} -> {item['target_tests']}"
              + ("" if item["ok"] else f" — FAIL: {item['reason']}"))
    print("parity: " + ("PASS" if report["parity"] else "FAIL"))
    print("result: " + ("PASS" if report["pass"] else "FAIL"))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
