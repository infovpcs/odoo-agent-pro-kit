# tests/hooks/test_dispatcher.py
from __future__ import annotations
import json
import importlib.util
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "odoo_hook.py"
_spec = importlib.util.spec_from_file_location("odoo_hook", _MOD_PATH)
odoo_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(odoo_hook)


def _run(event, payload):
    return odoo_hook.main([event], json.dumps(payload))


def test_no_op_outside_module(tmp_path):
    assert _run("PreToolUse", {"cwd": str(tmp_path), "tool_name": "Bash",
                               "tool_input": {"command": "python odoo-bin -i sale"}}) == 0


def _module(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    (mod / "views").mkdir()
    (tmp_path / ".git").mkdir()
    return mod


def test_pretooluse_blocks_raw_odoo_bin(tmp_path):
    mod = _module(tmp_path)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "python3 odoo-bin -d x -i sale"}})
    assert rc == 2


def test_pretooluse_allows_sandboxctl(tmp_path):
    mod = _module(tmp_path)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "sandbox/bin/sandboxctl module s-1 install mymod"}})
    assert rc == 0


def test_posttooluse_blocks_tree_on_19(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "19")
    mod = _module(tmp_path)
    rc = _run("PostToolUse", {"cwd": str(mod), "tool_name": "Write",
                              "tool_input": {"file_path": str(mod / "views" / "v.xml"),
                                             "content": "<odoo><tree/></odoo>"}})
    assert rc == 2


def test_userpromptsubmit_blocks_testing_incomplete(tmp_path):
    mod = _module(tmp_path)
    rc = _run("UserPromptSubmit", {"cwd": str(mod), "prompt": "/testing 19 mymod"})
    assert rc == 2


def test_stop_honours_active_flag(tmp_path):
    mod = _module(tmp_path)
    assert _run("Stop", {"cwd": str(mod), "stop_hook_active": True}) == 0


def test_bad_json_fails_open():
    assert odoo_hook.main(["PreToolUse"], "not json{") == 0


def test_unknown_event_fails_open(tmp_path):
    assert _run("Nonsense", {"cwd": str(tmp_path)}) == 0
