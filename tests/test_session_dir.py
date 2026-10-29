"""N10.7: in a hosted Hermes the kit's hooks use the chat's folder, not Hermes's cwd."""
import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def plugin(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    mod = importlib.import_module("plugin")
    yield mod
    for name in ("tools", "tools.file_tools_paths", "agent", "agent.runtime_cwd"):
        sys.modules.pop(name, None)


def _fake_hermes(monkeypatch, task_root=None, scope_root=None):
    tools = types.ModuleType("tools")
    ftp = types.ModuleType("tools.file_tools_paths")
    ftp._authoritative_workspace_root = lambda task_id="default": task_root
    agent = types.ModuleType("agent")
    rc = types.ModuleType("agent.runtime_cwd")
    rc.scope_terminal_cwd = lambda: scope_root
    for name, mod in (("tools", tools), ("tools.file_tools_paths", ftp), ("agent", agent), ("agent.runtime_cwd", rc)):
        monkeypatch.setitem(sys.modules, name, mod)


def test_uses_the_session_folder_when_visible(plugin, monkeypatch, tmp_path):
    chat = tmp_path / "projects" / "odoo20"
    chat.mkdir(parents=True)
    _fake_hermes(monkeypatch, task_root=str(chat))
    assert plugin._session_dir("t1") == chat


def test_falls_back_to_the_scope_then_cwd(plugin, monkeypatch, tmp_path):
    _fake_hermes(monkeypatch, task_root="/no/such/folder", scope_root=str(tmp_path))
    assert plugin._session_dir("t1") == tmp_path
    _fake_hermes(monkeypatch, task_root="~/x", scope_root=None)
    assert plugin._session_dir() == Path.cwd()


def test_outside_hermes_is_cwd(plugin):
    assert plugin._session_dir() == Path.cwd()
