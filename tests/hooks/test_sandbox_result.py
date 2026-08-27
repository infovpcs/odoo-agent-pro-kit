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
