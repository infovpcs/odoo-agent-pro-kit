import importlib.machinery
import importlib.util
import json
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_fleet():
    path = ROOT / "sandbox/bin/sandbox-fleet"
    loader = importlib.machinery.SourceFileLoader("sandbox_fleet", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_fleet_entrypoint_and_policy_are_bounded():
    fleet = ROOT / "sandbox/bin/sandbox-fleet"
    assert fleet.stat().st_mode & stat.S_IXUSR
    help_result = subprocess.run([str(fleet), "--help"], capture_output=True, text=True, check=True)
    for command in ("create", "status", "run", "cancel", "protect", "destroy", "maintain"):
        assert command in help_result.stdout
    config = json.loads((ROOT / "sandbox/config/concurrency.json").read_text())
    assert config["max_active_sessions"] == 6
    assert config["idle_stop_minutes"] == 60
    assert config["stopped_retention_days"] == 7
    assert config["artifact_retention_days"] == 14


def test_names_and_branches_are_normalized_and_unique():
    fleet = load_fleet()
    first = fleet.session_name("19.0", "Sale_Custom", "abc123")
    second = fleet.session_name("19", "Sale_Custom", "def456")
    assert first == "odoo-19-sale-custom-abc123"
    assert second == "odoo-19-sale-custom-def456"
    assert fleet.branch_name(first) == f"sandbox/{first}"


def test_port_parser_accepts_sbx_loopback_mapping():
    fleet = load_fleet()
    assert fleet.parse_port("8069/tcp -> 127.0.0.1:49152") == 49152
    assert fleet.parse_port("no published ports") is None


def test_create_requires_successful_port_publication():
    fleet = (ROOT / "sandbox/bin/sandbox-fleet").read_text()
    assert 'if port_result.returncode != 0 or not host_port:' in fleet
    assert 'raise RuntimeError(f"required Odoo port publication failed:' in fleet
    assert '["sbx", "rm", "--force", name]' in fleet
    assert "outer_creation_attempted = True" in fleet
    assert '"outer_removed": outer_creation_attempted and' in fleet
    assert "RuntimeError, KeyboardInterrupt" in fleet
    assert "signal.signal(signal.SIGINT, signal.SIG_IGN)" in fleet
    assert "signal.signal(signal.SIGINT, previous_sigint)" in fleet
    assert "data = None\n    try:\n        with controller_lock():" in fleet
    assert "if data is None:\n            raise" in fleet


def test_capacity_counts_retained_failures(monkeypatch):
    fleet = load_fleet()
    monkeypatch.setattr(fleet, "policy", lambda: {"max_active_sessions": 2})
    sessions = [{"status": "ready"}, {"status": "stopped"}]
    fleet.require_capacity(sessions)
    sessions[1]["status"] = "failed"
    try:
        fleet.require_capacity(sessions)
    except RuntimeError as error:
        assert "limit" in str(error)
    else:
        raise AssertionError("active-session limit was not enforced")
    sessions[1]["cleanup"] = {"outer_removed": True}
    fleet.require_capacity(sessions)


def test_cleanup_guard_requires_recoverable_work(monkeypatch, tmp_path):
    fleet = load_fleet()
    fleet.SESSIONS = tmp_path
    data = {
        "session_id": "odoo-19-sandbox-fixture-abc123", "status": "ready",
        "cleanup_guard": {"commit": False, "push": False, "patch_export": False},
    }
    fleet.write_session(data)
    args = type("Args", (), {"session": data["session_id"], "force": False})()
    try:
        fleet.cmd_destroy(args)
    except RuntimeError as error:
        assert "cleanup refused" in str(error)
    else:
        raise AssertionError("unprotected cleanup was allowed")


def test_compose_enforces_inner_resource_limits():
    compose = (ROOT / "sandbox/compose/compose.yaml").read_text()
    assert "ODOO_MEMORY_LIMIT" in compose
    assert "POSTGRES_MEMORY_LIMIT" in compose
    assert "ODOO_CPU_LIMIT" in compose
    assert "POSTGRES_CPU_LIMIT" in compose


def test_inner_controller_serializes_mutations_and_guards_destroy():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert "fcntl.flock(stream, fcntl.LOCK_EX)" in controller
    assert "destroy refused: export, commit/push externally" in controller
    assert "--allow-unexported" in controller
    assert "elif not directory.is_dir()" in controller
    assert "except FileExistsError" in controller


def test_outer_cleanup_retains_sandbox_when_inner_cleanup_fails():
    fleet = (ROOT / "sandbox/bin/sandbox-fleet").read_text()
    assert "inner cleanup failed" in fleet
    assert 'run(["sbx", "rm", "--force", args.session]' in fleet
