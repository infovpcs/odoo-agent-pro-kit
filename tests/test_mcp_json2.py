"""MCP connectivity to Odoo 19/20 Community through the External JSON-2 API.

Odoo's own MCP server (`ai_mcp`) is Enterprise-only (OEEL-1, depends `ai`), so on
Community the kit's MCP server talks to Odoo directly. Odoo 19+ ships
`POST /json/2/<model>/<method>` (addons/rpc/controllers/json2.py, `auth='bearer'`,
`bearer_scope='rpc'`); `/jsonrpc` and `/xmlrpc` still answer on 20 but log a
deprecation warning and are scheduled for removal in Odoo 22.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("requests")

from plugin.odoo_mcp.config import OdooConfig, load_config  # noqa: E402
from plugin.odoo_mcp.protocol_handlers import (  # noqa: E402
    Json2Client,
    JsonRpc20Client,
    XmlRpcClient,
    create_client,
)

REPO = Path(__file__).resolve().parents[1]
MANAGE = REPO / "odoo_local_setup" / "manage_modules.sh"
LAUNCHER = REPO / "plugin" / "odoo_mcp" / "start_mcp_server.sh"

_ENV_KEYS = [f"ODOO{p}_{k}" for p in ("", "17", "18", "19", "20")
             for k in ("URL", "DB_NAME", "DB_USER", "DB_PASSWORD", "API_KEY")]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in _ENV_KEYS + ["ODOO_RPC_PROTOCOL"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SANDBOX_SESSION_FILE", "/nonexistent/session.json")


# --- config: protocol selection ------------------------------------------------

def test_api_key_selects_json2_on_20(monkeypatch):
    monkeypatch.setenv("ODOO20_API_KEY", "k" * 40)
    cfg = load_config("20.0")
    assert cfg.protocol == "json-2"
    assert cfg.api_key == "k" * 40


def test_api_key_selects_json2_on_19(monkeypatch):
    monkeypatch.setenv("ODOO_API_KEY", "k" * 40)
    assert load_config("19.0").protocol == "json-2"


def test_no_api_key_keeps_legacy_jsonrpc_on_20():
    cfg = load_config("20.0")
    assert cfg.protocol == "json-rpc-2.0"
    assert cfg.api_key == ""


def test_api_key_ignored_before_19(monkeypatch):
    monkeypatch.setenv("ODOO18_API_KEY", "k" * 40)
    assert load_config("18.0").protocol == "xml-rpc"


def test_version_specific_key_wins_over_generic(monkeypatch):
    monkeypatch.setenv("ODOO_API_KEY", "generic")
    monkeypatch.setenv("ODOO20_API_KEY", "twenty")
    assert load_config("20.0").api_key == "twenty"


def test_factory_builds_json2_client():
    base = dict(database="odoo20", password="", odoo_version="20.0")
    assert isinstance(create_client(OdooConfig(protocol="json-2", api_key="x", **base)), Json2Client)
    assert isinstance(create_client(OdooConfig(protocol="json-rpc-2.0", **base)), JsonRpc20Client)
    assert isinstance(create_client(OdooConfig(protocol="xml-rpc", **base)), XmlRpcClient)


def test_json2_repr_does_not_leak_api_key():
    cfg = OdooConfig(database="odoo20", password="", protocol="json-2", api_key="s3cr3t-key")
    assert "s3cr3t-key" not in repr(cfg)
    assert "s3cr3t-key" not in str(cfg)


# --- Json2Client wire format -------------------------------------------------------

class _Resp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": {**self.headers, **(headers or {})}})
        return self.responses.pop(0)

    def close(self):
        pass


def _client(responses):
    cfg = OdooConfig(host="localhost", port=8110, database="odoo20", password="",
                     odoo_version="20.0", protocol="json-2", api_key="abc123")
    client = Json2Client(cfg)
    client.session = _Session(responses)
    client.session.headers.update(client._headers())
    return client


def test_json2_authenticate_uses_context_get_bearer_and_db_header():
    c = _client([_Resp(200, {"lang": "en_US", "tz": False, "uid": 2})])
    assert c.authenticate() == 2
    call = c.session.calls[0]
    assert call["url"] == "http://localhost:8110/json/2/res.users/context_get"
    assert call["headers"]["Authorization"] == "bearer abc123"
    assert call["headers"]["X-Odoo-Database"] == "odoo20"


def test_json2_search_read_sends_named_arguments():
    c = _client([_Resp(200, {"uid": 2}), _Resp(200, [{"id": 1, "model": "res.partner"}])])
    out = c.search_read("ir.model", domain=[["model", "=", "res.partner"]], fields=["model"], limit=1)
    assert out == [{"id": 1, "model": "res.partner"}]
    call = c.session.calls[-1]
    assert call["url"].endswith("/json/2/ir.model/search_read")
    assert call["json"] == {"domain": [["model", "=", "res.partner"]], "fields": ["model"], "limit": 1}


def test_json2_record_methods_pass_ids():
    c = _client([_Resp(200, {"uid": 2}), _Resp(200, True), _Resp(200, [{"id": 7}]), _Resp(200, True)])
    assert c.write("res.partner", [7], {"name": "X"}) is True
    assert c.session.calls[-1]["json"] == {"ids": [7], "vals": {"name": "X"}}
    c.read("res.partner", [7], ["name"])
    assert c.session.calls[-1]["json"] == {"ids": [7], "fields": ["name"]}
    c.unlink("res.partner", [7])
    assert c.session.calls[-1]["json"] == {"ids": [7]}


def test_json2_create_and_fields_get():
    c = _client([_Resp(200, {"uid": 2}), _Resp(200, [9]), _Resp(200, {"name": {"type": "char"}})])
    assert c.create("res.partner", {"name": "X"}) == 9
    assert c.session.calls[-1]["json"] == {"vals_list": [{"name": "X"}]}
    assert c.fields_get("res.partner", ["type"]) == {"name": {"type": "char"}}
    assert c.session.calls[-1]["json"] == {"attributes": ["type"]}


def test_json2_generic_execute_kw_maps_positional_args():
    c = _client([_Resp(200, {"uid": 2}), _Resp(200, 3)])
    assert c.execute_kw("res.partner", "search_count", [[["active", "=", True]]]) == 3
    assert c.session.calls[-1]["json"] == {"domain": [["active", "=", True]]}


def test_json2_unknown_positional_method_is_rejected_not_guessed():
    c = _client([_Resp(200, {"uid": 2})])
    result = c.execute_kw("res.partner", "some_custom_method", [1, 2])
    assert "error" in result and "keyword" in result["error"]


def test_json2_http_error_is_reported():
    c = _client([_Resp(401, {"name": "werkzeug.exceptions.Unauthorized", "message": "Invalid apikey"})])
    assert c.authenticate() is None
    c2 = _client([_Resp(200, {"uid": 2}),
                  _Resp(404, {"name": "werkzeug.exceptions.NotFound", "message": "the model 'x' does not exist"})])
    out = c2.search_read("x")
    assert out == {"error": "the model 'x' does not exist"}


# --- launcher + manage_modules.sh wiring -------------------------------------------

def test_launcher_passes_api_key_per_version():
    body = LAUNCHER.read_text()
    # Both the single-version and the --all start paths hand the key to the server.
    assert body.count('ODOO_API_KEY="$odoo_api_key"') == 2
    assert body.count('resolve_odoo_target "') == 2


def test_launcher_env_file_does_not_override_caller_env(tmp_path):
    body = LAUNCHER.read_text()
    fn = body[body.index("load_env() {"):body.index("# Check if server is already running")]
    env_file = tmp_path / ".env"
    env_file.write_text("ODOO20_URL=http://from-file:1\nODOO20_DB_NAME=from_file\n")
    script = ("print_status(){ :; }; print_warning(){ :; }\n" + fn +
              f'\nCONFIG_FILE="{env_file}"; load_env; echo "$ODOO20_URL|$ODOO20_DB_NAME"')
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True,
                         env={"PATH": "/usr/bin:/bin", "ODOO20_URL": "http://caller:8110"})
    assert out.stdout.strip() == "http://caller:8110|from_file"


def test_launcher_env_file_is_overridable():
    assert 'CONFIG_FILE="${MCP_ENV_FILE:-$PROJECT_DIR/.env}"' in LAUNCHER.read_text()


def test_manage_modules_finds_kit_from_workspace_env(tmp_path):
    kit = tmp_path / "kit"
    (kit / "plugin" / "odoo_mcp").mkdir(parents=True)
    (kit / "plugin" / "odoo_mcp" / "start_mcp_server.sh").write_text("#!/bin/bash\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".env").write_text(f"ODOO_AGENT_PRO_KIT_HOME={kit}\n")
    body = MANAGE.read_text()
    helpers = body[body.index("get_env_file_value() {"):body.index("# Version-specific defaults.")]
    fn = body[body.index("resolve_mcp_script() {"):body.index("# MAIN EXECUTION")]
    script = helpers + fn + f'\nPROJECT_DIR="{ws}"; WORKSPACE_PATH="{ws}"; resolve_mcp_script'
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                         env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)})
    assert out.stdout.strip() == str(kit / "plugin" / "odoo_mcp" / "start_mcp_server.sh")


def test_manage_modules_exports_workspace_mcp_env_and_apikey_command():
    body = MANAGE.read_text()
    assert "run_mcp_script()" in body
    assert 'MCP_ENV_FILE="$PROJECT_DIR/.env"' in body
    assert '"mcp-apikey")' in body
    # The key is generated with scope 'rpc': the only scope /json/2 accepts.
    assert "_generate('rpc'" in body or '_generate("rpc"' in body


def test_setup_local_macos_records_kit_home_for_mcp_discovery():
    body = (REPO / "odoo_local_setup" / "setup_local_macos.sh").read_text()
    assert "ODOO_AGENT_PRO_KIT_HOME=" in body and 'chmod 600 "${env_file}"' in body


def test_launcher_installs_its_own_requirements_file():
    body = LAUNCHER.read_text()
    assert (LAUNCHER.parent / "requirements.txt").is_file()
    assert '-r "$SCRIPT_DIR/requirements.txt"' in body
    assert "requirements.txt --python \"$VENV_DIR/bin/python\" 2>/dev/null || true" not in body
