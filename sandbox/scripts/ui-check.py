#!/usr/bin/env python3
"""Live UI check of Odoo screens with agent-browser (no LLM): the /testing acceptance rule as a script.

Backend parity is necessary but not sufficient for a migration (Phase 11 finding 9: the live UI
test found seven Odoo 20 bugs that the backend tests and parity missed). A screen passes only when
all four are clean after it loads:
  - `agent-browser errors` reports no page error;
  - `agent-browser console` has no `[error]` line (cleared before each open; missing JS modules
    only show up here);
  - the page has no error dialog or error page text;
  - the Odoo server log got no new `odoo.http` exception or traceback while the screen loaded.

Exit 0 when every screen passes, 1 when one fails, 2 on a usage error. The JSON result is what a
migration's `"ui_check": {"passed": ..., "result": ...}` progress record cites.

Usage: ui-check.py --base-url URL --path /odoo/crm [--path ...] --server-log ODOO_LOG
                   [--login admin --runtime-env .sandbox/sessions/<s>/runtime.env]
                   [--screenshot-dir DIR] [--settle SECONDS] [--json FILE]
Set AGENT_BROWSER to use another agent-browser binary; AGENT_BROWSER_SESSION keeps its session.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DIALOG = re.compile(r"Internal Server Error|Odoo Server Error|Oops|Something went wrong|Access Error|"
                    r"Invalid Operation|Missing Record|UncaughtPromiseError|Traceback")
SERVER_ERROR = re.compile(r"ERROR .*odoo\.http: Exception|Traceback")
SERVER_NOISE = re.compile(r"cursor already closed|connection already closed")
NO_ERRORS = re.compile(r"^\s*$|No errors|^\[\]$")


def browser(*args):
    binary = os.environ.get("AGENT_BROWSER", "agent-browser")
    return subprocess.run([binary, *args], capture_output=True, text=True).stdout


def log_lines(path):
    try:
        return Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return []


def password_from(runtime_env):
    for line in Path(runtime_env).read_text().splitlines():
        if line.startswith("ODOO_API_PASSWORD="):
            return line.split("=", 1)[1]
    raise SystemExit(f"no ODOO_API_PASSWORD in {runtime_env}")


def login(base_url, user, password, settle):
    browser("open", f"{base_url}/web/login")
    time.sleep(settle)
    browser("fill", "input[name=login]", user)
    browser("fill", "input[name=password]", password)
    browser("press", "Enter")
    time.sleep(settle)
    # Every screen would otherwise show the login page and pass vacuously.
    if "/web/login" in browser("get", "url"):
        raise SystemExit("ui-check: login failed (still on /web/login); check --login and --runtime-env")


def check_screen(url, server_log, settle, screenshot=None):
    before = len(log_lines(server_log))
    browser("console", "--clear")
    browser("open", url)
    time.sleep(settle)
    console = [line for line in browser("console").splitlines() if line.startswith("[error]")]
    page = [line for line in browser("errors").splitlines() if not NO_ERRORS.search(line)]
    dialog = [line.strip() for line in browser("snapshot").splitlines() if DIALOG.search(line)]
    server = [line for line in log_lines(server_log)[before:] if SERVER_ERROR.search(line) and not SERVER_NOISE.search(line)]
    if screenshot:
        browser("screenshot", str(screenshot))
    return {"url": url, "ok": not (console or page or dialog or server), "console_errors": console,
            "page_errors": page, "dialog_errors": dialog, "server_errors": server,
            "screenshot": str(screenshot) if screenshot else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--base-url", required=True, help="Odoo URL reachable from this host, e.g. http://127.0.0.1:8718")
    parser.add_argument("--path", action="append", default=[], help="screen to check, e.g. /odoo/crm (repeatable)")
    parser.add_argument("--server-log", required=True, help="the session's odoo.log (.sandbox/sessions/<s>/logs/odoo.log)")
    parser.add_argument("--login", help="log in as this user first")
    parser.add_argument("--runtime-env", help="session runtime.env holding the login password (never printed)")
    parser.add_argument("--screenshot-dir", help="save one screenshot per screen here")
    parser.add_argument("--settle", type=float, default=4.0, help="seconds to wait after each load (Odoo never reaches networkidle)")
    parser.add_argument("--json", metavar="FILE", help="write the result here")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return exit_.code
    if not args.path:
        print("ui-check: give at least one --path", file=sys.stderr)
        return 2
    if args.login and not args.runtime_env:
        print("ui-check: --login needs --runtime-env (the password is never passed on the command line)", file=sys.stderr)
        return 2
    base = args.base_url.rstrip("/")
    if args.login:
        try:
            login(base, args.login, password_from(args.runtime_env), args.settle)
        except SystemExit as failure:
            print(failure, file=sys.stderr)
            return 1
    # Absolute: agent-browser's daemon resolves a relative path against its own working directory.
    shots = Path(args.screenshot_dir).resolve() if args.screenshot_dir else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    checks = []
    for number, path in enumerate(args.path, 1):
        name = re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_") or "root"
        shot = shots / f"{number:02d}_{name}.png" if shots else None
        checks.append(check_screen(base + path, args.server_log, args.settle, shot))
    report = {"schema_version": "1.0.0", "base_url": base, "passed": all(c["ok"] for c in checks), "checks": checks}
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n")
    for check in checks:
        problems = [f"{kind}: {items[0]}" for kind, items in (("console", check["console_errors"]), ("page", check["page_errors"]),
                    ("dialog", check["dialog_errors"]), ("server", check["server_errors"])) if items]
        print(f"{'OK  ' if check['ok'] else 'FAIL'} {check['url']}" + ("" if check["ok"] else " — " + "; ".join(problems)))
    print("ui-check: " + ("PASS" if report["passed"] else "FAIL"))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
