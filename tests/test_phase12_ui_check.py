"""Phase 12 (finding 9): the live UI check as a kit script, driven here by a fake agent-browser."""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sandbox/scripts/ui-check.py"

FAKE = r'''#!/bin/sh
echo "$*" >> "$FAKE_AB_CALLS"
case "$1" in
  console) [ "$2" = "--clear" ] && exit 0; [ -n "$FAKE_CONSOLE" ] && printf '%s\n' "$FAKE_CONSOLE"; echo "[log] ready";;
  errors) [ -n "$FAKE_ERRORS" ] && printf '%s\n' "$FAKE_ERRORS" || echo "No errors";;
  snapshot) echo "- heading \"Leads\""; [ -n "$FAKE_PAGE" ] && printf '%s\n' "$FAKE_PAGE";;
  get) [ "$2" = url ] && echo "${FAKE_URL:-http://127.0.0.1:8718/odoo}";;
  open) [ -n "$FAKE_SERVER_LINE" ] && printf '%s\n' "$FAKE_SERVER_LINE" >> "$FAKE_SERVER_LOG";;
esac
exit 0
'''


def setup(tmp_path, **env):
    fake = tmp_path / "agent-browser"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "odoo.log"
    log.write_text("2026-09-29 10:00:00,000 1 INFO db odoo.modules.loading: ok\n")
    calls = tmp_path / "calls.txt"
    full_env = {**os.environ, "AGENT_BROWSER": str(fake), "FAKE_AB_CALLS": str(calls), "FAKE_SERVER_LOG": str(log), **env}
    return full_env, log, calls


def run(tmp_path, env, log, *extra):
    out = tmp_path / "ui.json"
    result = subprocess.run([sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:8718", "--path", "/odoo/crm",
                             "--path", "/odoo/project", "--server-log", str(log), "--settle", "0", "--json", str(out), *extra],
                            capture_output=True, text=True, env=env)
    return result, (json.loads(out.read_text()) if out.exists() else None)


def test_clean_screens_pass(tmp_path):
    env, log, calls = setup(tmp_path)
    result, report = run(tmp_path, env, log)
    assert result.returncode == 0, result.stdout + result.stderr
    assert report["passed"] is True and [c["url"] for c in report["checks"]] == ["http://127.0.0.1:8718/odoo/crm", "http://127.0.0.1:8718/odoo/project"]
    lines = calls.read_text().splitlines()
    assert lines.index("console --clear") < lines.index("open http://127.0.0.1:8718/odoo/crm")


def test_console_error_fails(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_CONSOLE="[error] Missing dependencies: @mymod/widget")
    result, report = run(tmp_path, env, log)
    assert result.returncode == 1
    assert report["checks"][0]["console_errors"] == ["[error] Missing dependencies: @mymod/widget"]


def test_page_error_fails(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_ERRORS="TypeError: x is undefined")
    result, report = run(tmp_path, env, log)
    assert result.returncode == 1 and report["checks"][0]["page_errors"] == ["TypeError: x is undefined"]


def test_error_dialog_fails(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_PAGE='- dialog "Odoo Server Error"')
    result, report = run(tmp_path, env, log)
    assert result.returncode == 1 and report["checks"][0]["dialog_errors"]


def test_new_server_exception_fails_but_old_ones_do_not(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_SERVER_LINE="2026-09-29 10:00:01,000 1 ERROR db odoo.http: Exception during request handling.")
    log.write_text(log.read_text() + "2026-09-29 09:00:00,000 1 ERROR db odoo.http: Exception during request handling.\n")
    result, report = run(tmp_path, env, log)
    assert result.returncode == 1
    assert len(report["checks"][0]["server_errors"]) == 1


def test_closed_cursor_noise_is_ignored(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_SERVER_LINE="2026-09-29 10:00:01,000 1 ERROR db odoo.http: Exception: cursor already closed")
    result, report = run(tmp_path, env, log)
    assert result.returncode == 0, report


def test_login_uses_the_session_password_without_printing_it(tmp_path):
    env, log, calls = setup(tmp_path)
    session = tmp_path / "sessions/s1"
    session.mkdir(parents=True)
    (session / "runtime.env").write_text("ODOO_API_PASSWORD=s3cret-value\n")
    result, report = run(tmp_path, env, log, "--login", "admin", "--runtime-env", str(session / "runtime.env"))
    assert result.returncode == 0, result.stderr
    text = calls.read_text()
    assert "open http://127.0.0.1:8718/web/login" in text and "fill input[name=password] s3cret-value" in text
    assert "s3cret-value" not in result.stdout + result.stderr + json.dumps(report)


def test_screenshots_are_taken_per_screen(tmp_path):
    env, log, calls = setup(tmp_path)
    result, _ = run(tmp_path, env, log, "--screenshot-dir", str(tmp_path / "shots"))
    assert result.returncode == 0
    assert f"screenshot {tmp_path / 'shots'}/01_odoo_crm.png" in calls.read_text()


def test_no_screens_is_a_usage_error(tmp_path):
    env, log, _ = setup(tmp_path)
    result = subprocess.run([sys.executable, str(SCRIPT), "--base-url", "http://x", "--server-log", str(log)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 2


def test_relative_screenshot_dir_is_passed_as_an_absolute_path(tmp_path):
    # agent-browser's daemon resolves relative paths against its own working directory.
    env, log, calls = setup(tmp_path)
    out = tmp_path / "ui.json"
    result = subprocess.run([sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:8718", "--path", "/odoo/crm",
                             "--server-log", str(log), "--settle", "0", "--json", str(out), "--screenshot-dir", "shots"],
                            capture_output=True, text=True, env=env, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert f"screenshot {tmp_path.resolve() / 'shots'}/01_odoo_crm.png" in calls.read_text()


def test_a_login_that_stays_on_the_login_page_fails(tmp_path):
    env, log, _ = setup(tmp_path, FAKE_URL="http://127.0.0.1:8718/web/login")
    session = tmp_path / "runtime.env"
    session.write_text("ODOO_API_PASSWORD=x\n")
    result, report = run(tmp_path, env, log, "--login", "admin", "--runtime-env", str(session))
    assert result.returncode == 1 and "login failed" in result.stdout + result.stderr
