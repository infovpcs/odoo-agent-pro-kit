"""Regression tests for GitHub issues #3 and #4.

#3: `module test` on a module that is not installed, or a run that executes no
tests, must not report success, and junit.xml must carry the real totals.
#4: the operation log named in a failed result must hold the Odoo error, and
the result must name odoo.log and carry the error line in `error.summary`.
"""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FAKE_DOCKER = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$FAKE_DOCKER_LOG"
if [[ "$*" == *psql* ]]; then
    [[ -f "$FAKE_INSTALLED_FLAG" ]] && echo 1
    exit 0
fi
if [[ "$*" == *'odoo --config'* ]]; then
    [[ -f "$FAKE_ODOO_OUTPUT" ]] && cat "$FAKE_ODOO_OUTPUT" >> "$ODOO_LOG_FILE"
    exit "${FAKE_RUN_RC:-0}"
fi
exit 0
"""


def run_manage(tmp_path, operation, module="sandbox_fixture", installed=True, odoo_output=None, run_rc=0, prior_log=""):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(exist_ok=True)
    docker = fake_bin / "docker"
    docker.write_text(FAKE_DOCKER)
    docker.chmod(0o755)
    (tmp_path / "compose.yaml").write_text("services: {}\n")
    (tmp_path / "runtime.env").write_text("POSTGRES_USER=odoo_runtime\n")
    logs = tmp_path / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "odoo.log").write_text(prior_log)
    if installed:
        (tmp_path / "installed.flag").write_text("")
    if odoo_output is not None:
        (tmp_path / "odoo_output.log").write_text(odoo_output)
    env = os.environ.copy()
    env.update({
        "PATH": f"{fake_bin}:{env['PATH']}", "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
        "FAKE_INSTALLED_FLAG": str(tmp_path / "installed.flag"),
        "FAKE_ODOO_OUTPUT": str(tmp_path / "odoo_output.log"), "FAKE_RUN_RC": str(run_rc),
        "ODOO_EXECUTOR": "compose", "ODOO_VERSION": "19", "ODOO_DB_NAME": "sandbox_db",
        "ODOO_EXEC_CONFIG_FILE": "/etc/odoo/odoo.conf", "ODOO_LOG_DIR": str(logs),
        "ODOO_LOG_FILE": str(logs / "odoo.log"),
        "ODOO_RESULTS_DIR": str(tmp_path / "results"), "ODOO_PROGRESS_FILE": str(tmp_path / "progress.json"),
        "SESSION_ID": "19-issue-test", "COMPOSE_FILE": str(tmp_path / "compose.yaml"),
        "COMPOSE_ENV_FILE": str(tmp_path / "runtime.env"), "POSTGRES_USER": "odoo_runtime",
    })
    proc = subprocess.run(
        ["bash", str(ROOT / "odoo_local_setup/manage_modules.sh"), operation, module],
        env=env, cwd=ROOT, capture_output=True, text=True,
    )
    results = list((tmp_path / "results").glob(f"{operation}-*.json"))
    assert len(results) == 1, (proc.stdout, proc.stderr)
    return proc, json.loads(results[0].read_text())


def summary_line(failed, errors, total):
    return (f"2026-10-15 10:00:00,000 1 INFO sandbox_db odoo.tests.result: {failed} failed, "
            f"{errors} error(s) of {total} tests when loading database 'sandbox_db'\n")


# --- issue #3 ---------------------------------------------------------------

def test_module_test_fails_when_module_is_not_installed(tmp_path):
    proc, data = run_manage(tmp_path, "test", installed=False, odoo_output=summary_line(0, 0, 0))
    assert proc.returncode != 0
    assert data["status"] == "failed"
    assert data["error"]["code"] == "module_not_installed"
    assert "sandbox_fixture" in data["error"]["summary"]
    assert "--test-enable" not in (tmp_path / "docker.log").read_text()


def test_module_test_fails_when_no_tests_executed(tmp_path):
    proc, data = run_manage(tmp_path, "test", odoo_output=summary_line(0, 0, 0))
    assert proc.returncode != 0
    assert data["status"] == "failed"
    assert data["error"]["code"] == "no_tests_executed"


def test_module_test_fails_when_odoo_prints_no_summary(tmp_path):
    proc, data = run_manage(tmp_path, "test", odoo_output="2026-10-15 INFO sandbox_db odoo.modules.loading: Modules loaded.\n")
    assert proc.returncode != 0
    assert data["error"]["code"] == "no_tests_executed"


def test_module_test_succeeds_and_reports_totals(tmp_path):
    proc, data = run_manage(tmp_path, "test", odoo_output=summary_line(0, 0, 28))
    assert proc.returncode == 0, proc.stdout
    assert data["status"] == "succeeded"
    assert data["message"] == "28 tests, 0 failed, 0 error(s)"


def test_module_test_fails_on_failed_tests_even_with_exit_zero(tmp_path):
    proc, data = run_manage(tmp_path, "test", odoo_output=summary_line(3, 4, 16))
    assert proc.returncode != 0
    assert data["error"]["code"] == "test_failed"
    assert data["message"] == "16 tests, 3 failed, 4 error(s)"


def test_module_test_uses_only_lines_written_during_the_run(tmp_path):
    proc, data = run_manage(tmp_path, "test", prior_log=summary_line(0, 0, 99),
                            odoo_output=summary_line(0, 0, 0))
    assert data["error"]["code"] == "no_tests_executed"


# --- issue #4 ---------------------------------------------------------------

TRACEBACK = (
    "2026-10-15 10:00:00,000 1 ERROR sandbox_db odoo.modules.loading: Failed to load module\n"
    "Traceback (most recent call last):\n"
    '  File "/mnt/extra-addons/sandbox_fixture/hooks.py", line 3, in post_init_hook\n'
    "    raise ValueError('boom from post_init_hook')\n"
    "ValueError: boom from post_init_hook\n"
)


def test_failed_install_operation_log_contains_the_odoo_traceback(tmp_path):
    proc, data = run_manage(tmp_path, "install", installed=False, odoo_output=TRACEBACK, run_rc=1,
                            prior_log="older line that is not part of this run\n")
    assert proc.returncode != 0
    operation_log = Path(data["logs"][0]).read_text()
    assert "Traceback (most recent call last)" in operation_log
    assert "ValueError: boom from post_init_hook" in operation_log
    assert "older line that is not part of this run" not in operation_log


def test_failed_install_result_names_odoo_log_and_error_line(tmp_path):
    _, data = run_manage(tmp_path, "install", installed=False, odoo_output=TRACEBACK, run_rc=1)
    assert str(tmp_path / "logs/odoo.log") in data["logs"]
    assert "ValueError: boom from post_init_hook" in data["error"]["summary"]
    reports = [Path(p) for p in data["logs"] if "errors_" in Path(p).name]
    assert reports and "boom from post_init_hook" in reports[0].read_text()


def test_failed_result_still_matches_the_operation_schema(tmp_path):
    jsonschema = __import__("pytest").importorskip("jsonschema")
    schema = json.loads((ROOT / "sandbox/schemas/operation-result.schema.json").read_text())
    for operation, kwargs in (("install", {"installed": False, "odoo_output": TRACEBACK, "run_rc": 1}),
                              ("test", {"odoo_output": summary_line(0, 0, 0)})):
        target = tmp_path / operation
        target.mkdir()
        _, data = run_manage(target, operation, **kwargs)
        jsonschema.validate(data, schema)


# --- issue #3: junit.xml ------------------------------------------------------

def load_controller(tmp_path):
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader("sandboxctl_issues", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    module.ROOT = tmp_path
    directory = module.state_dir("issue-session")
    for child in ("logs/test_results", "results", "diagnostics", "addons/sandbox_fixture",
                  "tests/junit", "tests/coverage", "tests/browser/screenshots"):
        (directory / child).mkdir(parents=True, exist_ok=True)
    (directory / "addons/sandbox_fixture/__manifest__.py").write_text("{'name': 'x'}\n")
    (directory / "runtime.env").write_text("ODOO_DB_NAME=sandbox_db\n")
    (directory / "session.json").write_text(json.dumps(
        {"session_id": "issue-session", "odoo_version": "19.0", "module": "sandbox_fixture", "status": "ready"}))
    return module, directory


def test_odoo_test_totals_reads_the_last_summary():
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader("sandboxctl_totals", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    controller = importlib.util.module_from_spec(spec)
    loader.exec_module(controller)
    text = summary_line(0, 0, 5) + "noise\n" + summary_line(3, 4, 16)
    assert controller.odoo_test_totals(text) == (16, 3, 4)
    assert controller.odoo_test_totals("no summary here\n") is None


def test_junit_carries_the_real_totals(tmp_path):
    controller, directory = load_controller(tmp_path)
    controller.write_test_artifacts("issue-session", "sandbox_fixture", 1, (16, 3, 4))
    junit = (directory / "tests/junit/junit.xml").read_text()
    assert 'tests="16"' in junit and 'failures="3"' in junit and 'errors="4"' in junit


def test_junit_reports_zero_tests_when_none_ran(tmp_path):
    controller, directory = load_controller(tmp_path)
    controller.write_test_artifacts("issue-session", "sandbox_fixture", 1, (0, 0, 0))
    junit = (directory / "tests/junit/junit.xml").read_text()
    assert 'tests="0"' in junit
    assert 'tests="1"' not in junit
    assert 'failures="1"' in junit


def test_module_test_writes_totals_from_the_operation_log(monkeypatch, tmp_path):
    controller, directory = load_controller(tmp_path)
    op_log = directory / "logs/test_results/test_20261015_100000.log"

    def fake_run(*_args, **_kwargs):
        op_log.write_text(summary_line(0, 0, 28))
        (directory / "results/test-1-1.json").write_text(json.dumps(
            {"operation": "test", "status": "succeeded", "logs": [str(op_log)]}))
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr(controller.subprocess, "run", fake_run)
    assert controller.module_operation("issue-session", "test", "sandbox_fixture") == 0
    assert 'tests="28"' in (directory / "tests/junit/junit.xml").read_text()
