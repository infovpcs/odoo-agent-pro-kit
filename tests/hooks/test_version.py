from __future__ import annotations
import json
from plugin.hooks.checks import version


def test_from_sandbox_session(tmp_path, monkeypatch):
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "session.json").write_text(json.dumps({"odoo_version": "18.0"}))
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) == "18"


def test_from_version_dir(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "19.0").mkdir()
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "19"


def test_from_module_meta(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "docs" / "module_meta.md").write_text("odoo_version: 17.0\n")
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "17"


def test_from_env_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "18.0")
    assert version.detect_odoo_version(tmp_path) == "18"


def test_none_when_nothing(tmp_path, monkeypatch):
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) is None


def test_malformed_session_json_falls_through(tmp_path, monkeypatch):
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "session.json").write_text("null")
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) is None
