"""Local (non-sandbox) workspace setup supports Odoo 20.0 alongside 17/18/19.

Odoo 20.0 needs Python >= 3.12 and PostgreSQL >= 16 (odoo/release.py
MIN_PY_VERSION / MIN_PG_VERSION on odoo/odoo@20.0), so the macOS setup must be able
to point a 20 workspace at a separate PostgreSQL 16 server.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SETUP = REPO / "odoo_local_setup"
MANAGE = SETUP / "manage_modules.sh"


def _manage_block(start: str, end: str) -> str:
    body = MANAGE.read_text()
    return body[body.index(start):body.index(end)]


def _detect(tmp_path: Path, dirs) -> str:
    for d in dirs:
        (tmp_path / d).mkdir()
    block = _manage_block('WORKSPACE_PATH="${WORKSPACE_PATH:-.}"', "# Colors for output")
    out = subprocess.run(["bash", "-c", block + '\necho "$ODOO_VERSION"'],
                         env={"WORKSPACE_PATH": str(tmp_path), "PATH": "/usr/bin:/bin"},
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def test_manage_modules_detects_20_workspace_first(tmp_path):
    assert _detect(tmp_path, ["20.0", "19.0"]) == "20"


@pytest.mark.parametrize("v", ["17", "18", "19"])
def test_manage_modules_still_detects_older_workspaces(tmp_path, v):
    assert _detect(tmp_path, [f"{v}.0"]) == v


def test_manage_modules_has_20_label_and_default_port():
    block = _manage_block("DEFAULT_PORT=", "# Create necessary directories")
    out = subprocess.run(["bash", "-c", "ODOO_VERSION=20\n" + block +
                          '\necho "$DEFAULT_PORT|$VERSION_LABEL"'],
                         capture_output=True, text=True, check=True)
    port, label = out.stdout.strip().split("|")
    assert port == "8110" and label.startswith("Odoo 20.0")


def test_odoo_conf_20_template():
    conf = (SETUP / "config" / "odoo.conf.20").read_text()
    for needle in ("db_name = odoo20", "dbfilter = ^odoo20$", "http_port = 8110",
                   "{{WORKSPACE_PATH}}/20.0/addons", "{{WORKSPACE_PATH}}/extra-20",
                   "db_port = {{DB_PORT}}", "db_host = {{DB_HOST}}", "cache_prefix = odoo_20"):
        assert needle in conf, needle


def test_setup_local_macos_accepts_versions_base_dir_and_db_port():
    script = (SETUP / "setup_local_macos.sh").read_text()
    for flag in ("--versions", "--base-dir", "--db-host", "--db-port", "--dry-run"):
        assert flag in script, flag
    out = subprocess.run(["bash", str(SETUP / "setup_local_macos.sh"), "--dry-run",
                          "--versions", "20", "--base-dir", "/tmp/ws-example", "--db-port", "5436"],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "20_workspace" in out.stdout and "5436" in out.stdout
    assert "17_workspace" not in out.stdout


def test_setup_local_macos_rejects_unknown_version():
    out = subprocess.run(["bash", str(SETUP / "setup_local_macos.sh"), "--dry-run", "--versions", "21"],
                         capture_output=True, text=True)
    assert out.returncode != 0


def test_mcp_launcher_default_odoo20_url_matches_workspace_port():
    body = (REPO / "plugin" / "odoo_mcp" / "start_mcp_server.sh").read_text()
    fn = body[body.index("resolve_odoo_target() {"):body.index("# Print colored message")]
    out = subprocess.run(["bash", "-c", fn + '\nresolve_odoo_target 20; echo "$ODOO_T_URL"'],
                         capture_output=True, text=True, check=True, env={"PATH": "/usr/bin:/bin"})
    assert out.stdout.strip() == "http://localhost:8110"
