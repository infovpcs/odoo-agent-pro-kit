from __future__ import annotations
from plugin.hooks.checks import authz


def test_env_grants(monkeypatch, tmp_path):
    monkeypatch.setenv("ODOO_KIT_ALLOW_VCS_WRITE", "1")
    assert authz.vcs_write_allowed(tmp_path) is True


def test_marker_grants(monkeypatch, tmp_path):
    monkeypatch.delenv("ODOO_KIT_ALLOW_VCS_WRITE", raising=False)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "AUTHORIZED").write_text("ok\n")
    assert authz.vcs_write_allowed(tmp_path) is True


def test_default_denied(monkeypatch, tmp_path):
    monkeypatch.delenv("ODOO_KIT_ALLOW_VCS_WRITE", raising=False)
    (tmp_path / ".git").mkdir()
    assert authz.vcs_write_allowed(tmp_path) is False
