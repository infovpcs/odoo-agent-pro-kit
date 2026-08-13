import importlib.machinery
import importlib.util
import json
import subprocess
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader("sandboxctl_phase6", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def fake_session(controller, tmp_path):
    controller.ROOT = tmp_path
    session = "phase6-session"
    directory = controller.state_dir(session)
    for child in ("logs", "results", "diagnostics", "tests/junit", "tests/coverage", "tests/browser/screenshots"):
        (directory / child).mkdir(parents=True, exist_ok=True)
    (directory / "runtime.env").write_text("POSTGRES_PASSWORD=hunter2\nODOO_API_KEY=abc123\n")
    (directory / "session.json").write_text(json.dumps({"session_id": session, "odoo_version": "19.0", "module": "sandbox_fixture"}))
    (directory / "events.jsonl").write_text('{"status":"failed","token":"abc123"}\n')
    (directory / "results/result.json").write_text('{"message":"password=hunter2"}\n')
    return session, directory


def test_phase6_commands_are_exposed():
    help_result = subprocess.run([str(ROOT / "sandbox/bin/sandboxctl"), "--help"], capture_output=True, text=True, check=True)
    for command in ("logs", "diagnose", "backup", "restore", "recover"):
        assert command in help_result.stdout


def test_redacted_diagnostic_bundle_has_stable_evidence(monkeypatch, tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)

    def completed(*_args, **_kwargs):
        return subprocess.CompletedProcess([], 0, stdout="password=hunter2 token=abc123\n", stderr="")

    monkeypatch.setattr(controller.subprocess, "run", completed)
    bundle = Path(controller.diagnostics(session, "denied-network"))
    assert bundle.parent == directory / "diagnostics"
    with tarfile.open(bundle) as archive:
        names = set(archive.getnames())
        assert {"bundle.json", "compose-state.json", "compose-processes.log", "resources.jsonl", "service-logs.log", "policy.json", "session.json", "events.jsonl", "results/result.json"} <= names
        content = b"".join(archive.extractfile(name).read() for name in names if archive.getmember(name).isfile())
    assert b"hunter2" not in content
    assert b"abc123" not in content
    assert b"[REDACTED]" in content


def test_stable_test_artifacts_are_machine_readable(tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    controller.write_test_artifacts(session, "sandbox_fixture", 1)
    assert "failures=\"1\"" in (directory / "tests/junit/junit.xml").read_text()
    assert "line-rate=\"0\"" in (directory / "tests/coverage/coverage.xml").read_text()
    assert json.loads((directory / "tests/browser/result.json").read_text())["status"] == "not_run"


def test_optional_telemetry_file_interface(tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    target = tmp_path / "otel/events.jsonl"
    (directory / "runtime.env").write_text(f"SANDBOX_OTEL_LOG_ENDPOINT=file://{target}\n")
    controller.emit_telemetry(session, "health", {"status": "recoverable"})
    record = json.loads(target.read_text())
    assert record["session_id"] == session
    assert record["attributes"]["status"] == "recoverable"


def test_failed_restore_keeps_odoo_stopped_and_marks_session_failed(monkeypatch, tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    (directory / "runtime.env").write_text("POSTGRES_USER=odoo\nODOO_DB_NAME=sandbox_db\n")
    backup = directory / "backups/failed.dump"
    backup.parent.mkdir()
    backup.write_bytes(b"not-a-valid-dump")
    compose_calls = []
    transitions = []
    results = []

    def fake_compose(_session, *args, **kwargs):
        compose_calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(controller, "compose", fake_compose)
    monkeypatch.setattr(controller.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 1))
    monkeypatch.setattr(controller, "diagnostics", lambda *args, **kwargs: "diagnostics.tar.gz")
    monkeypatch.setattr(controller, "transition", lambda *args, **kwargs: transitions.append((args, kwargs)))
    monkeypatch.setattr(controller, "result", lambda *args, **kwargs: results.append((args, kwargs)))

    try:
        controller.database_restore(session, backup)
    except RuntimeError as error:
        assert "restore failed" in str(error)
    else:
        raise AssertionError("invalid restore unexpectedly succeeded")

    assert compose_calls == [
        ("stop", "odoo"), ("ps", "-q", "odoo"), ("ps", "-q", "odoo"),
        ("stop", "odoo"), ("ps", "-q", "odoo"), ("ps", "-q", "odoo"),
    ]
    assert transitions[-1][0][1] == "failed"
    assert results[-1][0][3] == "failed"


def test_restore_quarantine_force_removes_running_odoo(monkeypatch):
    controller = load_controller()
    outputs = iter(["odoo-container\n", ""])
    removed = []

    def fake_compose(_session, *args, **kwargs):
        stdout = next(outputs) if args[:3] == ("ps", "-q", "odoo") else ""
        return subprocess.CompletedProcess(args, 1 if args[0] == "stop" else 0, stdout=stdout, stderr="")

    monkeypatch.setattr(controller, "compose", fake_compose)
    monkeypatch.setattr(controller.subprocess, "run", lambda command, **kwargs: removed.append(command) or subprocess.CompletedProcess(command, 0))
    controller.ensure_odoo_stopped("phase6-session")
    assert removed == [["docker", "rm", "--force", "odoo-container"]]


def test_restore_quarantine_failure_still_persists_failed_state(monkeypatch, tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    (directory / "runtime.env").write_text("POSTGRES_USER=odoo\nODOO_DB_NAME=sandbox_db\n")
    backup = directory / "backups/failed.dump"
    backup.parent.mkdir()
    backup.write_bytes(b"not-a-valid-dump")
    transitions = []
    results = []
    stack_quarantines = []

    def fake_quarantine(_session):
        raise RuntimeError("container remains running")

    monkeypatch.setattr(controller, "ensure_odoo_stopped", fake_quarantine)
    monkeypatch.setattr(controller, "ensure_stack_stopped", lambda session: stack_quarantines.append(session))
    monkeypatch.setattr(controller.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 1))
    monkeypatch.setattr(controller, "diagnostics", lambda *args, **kwargs: "diagnostics.tar.gz")
    monkeypatch.setattr(controller, "transition", lambda *args, **kwargs: transitions.append((args, kwargs)))
    monkeypatch.setattr(controller, "result", lambda *args, **kwargs: results.append((args, kwargs)))

    try:
        controller.database_restore(session, backup)
    except RuntimeError as error:
        assert "container remains running" in str(error)
    else:
        raise AssertionError("invalid restore unexpectedly succeeded")

    assert transitions[0][0][1] == "failed"
    assert transitions[-1][1]["failure"]["quarantine"] == "stack_stopped"
    assert "container remains running" in transitions[-1][1]["failure"]["quarantine_error"]
    assert stack_quarantines == [session]
    assert results[-1][0][3] == "failed"
    assert (directory / "restore-blocked.json").is_file()


def test_recover_refuses_unsuccessful_restore(monkeypatch, tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    (directory / "restore-blocked.json").write_text("{}\n")
    compose_calls = []
    monkeypatch.setattr(controller, "compose", lambda *args, **kwargs: compose_calls.append(args))
    monkeypatch.setattr(controller, "diagnostics", lambda *args, **kwargs: "diagnostics.tar.gz")
    monkeypatch.setattr(controller, "transition", lambda *args, **kwargs: None)
    monkeypatch.setattr(controller, "result", lambda *args, **kwargs: None)

    try:
        controller.recover(session, 30)
    except RuntimeError as error:
        assert "complete an explicit restore first" in str(error)
    else:
        raise AssertionError("recovery bypassed the failed-restore integrity block")
    assert compose_calls == []


def test_restore_integrity_guard_blocks_direct_start(tmp_path):
    controller = load_controller()
    session, directory = fake_session(controller, tmp_path)
    (directory / "restore-blocked.json").write_text("{}\n")
    try:
        controller.require_restore_integrity(session, "start")
    except RuntimeError as error:
        assert "start blocked" in str(error)
    else:
        raise AssertionError("direct start bypassed the failed-restore integrity block")


def test_module_dispatch_enforces_restore_integrity():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert 'require_restore_integrity(args.session, f"module {args.operation}")' in controller
    assert 'require_restore_integrity(args.session, "exec")' in controller
    assert 'require_restore_integrity(args.session, "backup")' in controller


def test_failure_scenarios_have_bundle_and_recovery_contract():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    for scenario in ("create-failed", "readiness-timeout", "module-{operation}-failed", "{operation}-failed"):
        assert scenario in controller
    assert 'transition(session, "recoverable"' in controller
    assert "ensure_odoo_stopped(session)" in controller
    assert 'diagnostics(session, "interrupted-operation")' in controller
    assert 'diagnostics(session, "recovery-failed")' in controller
    assert "restore accepts only this session's backup artifacts" in controller
    assert 'diagnostics(session, "invalid-module")' in controller
    assert '"code": "invalid_module"' in controller
    assert 'diagnostics(session, "database-restore-failed")' in controller
    assert '"code": "restore_failed"' in controller
    assert 'transition(session, "failed", failure=' in controller
