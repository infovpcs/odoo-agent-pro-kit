from __future__ import annotations
import json, importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _load(rel):
    spec = importlib.util.spec_from_file_location(rel.replace("/", "_"), _ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_odoo_hook_all_events_exit_0_on_empty():
    oh = _load("plugin/hooks/odoo_hook.py")
    for ev in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        assert oh.main([ev], "{}") == 0


def test_contributor_hook_all_events_exit_0_on_empty():
    ch = _load("scripts/contributor_hook.py")
    for ev in ("SessionStart", "PreToolUse", "Stop"):
        assert ch.main([ev], "{}") == 0


def test_plugin_versions_match():
    j = json.loads((_ROOT / "plugin" / ".claude-plugin" / "plugin.json").read_text())
    y = (_ROOT / "plugin" / "plugin.yaml").read_text()
    assert j["version"] == "0.6.0"
    assert 'version: "0.6.0"' in y


def test_plugin_yaml_lists_five_hooks():
    y = (_ROOT / "plugin" / "plugin.yaml").read_text()
    for h in ("on_session_start", "on_session_end", "post_api_request", "pre_tool_call", "post_tool_call"):
        assert h in y
