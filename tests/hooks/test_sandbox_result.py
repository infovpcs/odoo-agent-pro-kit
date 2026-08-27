from __future__ import annotations
import json, time
from plugin.hooks.checks import sandbox_result


def _write(results_dir, operation, module, status, extra=None):
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0", "session_id": "s-abc", "operation_id": "op1",
        "operation": operation, "module": module, "attempt": 1, "status": status,
        "started_at": "2026-08-27T00:00:00Z", "finished_at": "2026-08-27T00:01:00Z",
        "duration_ms": 60000, "exit_code": 0 if status == "succeeded" else 1,
        "logs": [], "artifacts": [],
    }
    if extra:
        payload.update(extra)
    p = results_dir / f"{operation}-{int(time.time())}-{id(payload) % 9999}.json"
    p.write_text(json.dumps(payload))
    return p


def test_non_matching_command_returns_none(tmp_path):
    assert sandbox_result.read_operation_result("ls -la", tmp_path) is None


def test_reads_succeeded_install(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    _write(rd, "install", "mymod", "succeeded")
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc install mymod", tmp_path)
    assert r is not None and r.status == "succeeded" and r.module_state_ok is True


def test_reads_failed_install(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    _write(rd, "install", "mymod", "failed",
           extra={"error": {"code": "install_failed", "summary": "missing dep sale_renting_crm"}})
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc install mymod", tmp_path)
    assert r.status == "failed" and r.module_state_ok is False
    assert "sale_renting_crm" in r.reason


def test_picks_newest(tmp_path, monkeypatch):
    rd = tmp_path / "results"
    monkeypatch.setenv("ODOO_RESULTS_DIR", str(rd))
    old = _write(rd, "test", "mymod", "failed")
    import os
    os.utime(old, (1, 1))
    _write(rd, "test", "mymod", "succeeded")
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc test mymod", tmp_path)
    assert r.status == "succeeded"


def test_finds_session_via_kit_root_env(tmp_path, monkeypatch):
    """Module edited outside the kit repo: ODOO_KIT_SANDBOX_ROOT points home."""
    monkeypatch.delenv("ODOO_RESULTS_DIR", raising=False)
    kit = tmp_path / "odoo-agent-pro-kit"
    results = kit / ".sandbox" / "sessions" / "mig-x-18" / "results"
    _write(results, "test", "mymod", "succeeded")
    monkeypatch.setenv("ODOO_KIT_SANDBOX_ROOT", str(kit))

    module_dir = tmp_path / "vpcs_apps_cloud_18" / "mymod"
    module_dir.mkdir(parents=True)
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module mig-x-18 test mymod", module_dir)
    assert r is not None and r.status == "succeeded" and r.module_state_ok is True


def test_named_session_beats_newest_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("ODOO_RESULTS_DIR", raising=False)
    kit = tmp_path / "kit"
    (kit / ".sandbox").mkdir(parents=True)
    _write(kit / ".sandbox" / "sessions" / "old-sess" / "results", "install", "mymod", "failed")
    want = kit / ".sandbox" / "sessions" / "wanted-sess" / "results"
    _write(want, "install", "mymod", "succeeded")
    import os
    os.utime(kit / ".sandbox" / "sessions" / "wanted-sess", (1, 1))  # make it the OLDEST
    monkeypatch.setenv("ODOO_KIT_SANDBOX_ROOT", str(kit))
    r = sandbox_result.read_operation_result(
        "sandboxctl module wanted-sess install mymod", tmp_path)
    assert r is not None and r.status == "succeeded"


def test_malformed_session_json_uses_fallback_dir(tmp_path, monkeypatch):
    """Harden against non-dict JSON values in .sandbox/session.json"""
    monkeypatch.delenv("ODOO_RESULTS_DIR", raising=False)

    # Write malformed session.json with null value
    sandbox_dir = tmp_path / ".sandbox"
    sandbox_dir.mkdir()
    (sandbox_dir / "session.json").write_text("null")

    # Write result file to fallback dir
    fallback_results = tmp_path / "logs" / "test_results"
    _write(fallback_results, "install", "mymod", "succeeded")

    # Should fall back to logs/test_results/ and find the result
    r = sandbox_result.read_operation_result(
        "sandbox/bin/sandboxctl module s-abc install mymod", tmp_path)
    assert r is not None
    assert r.status == "succeeded"
    assert r.module_state_ok is True
