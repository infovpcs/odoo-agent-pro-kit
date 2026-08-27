from __future__ import annotations
from plugin.hooks.checks import hermes_adapter


def _module(tmp_path):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    (tmp_path / ".git").mkdir()
    return mod


def test_pre_tool_call_blocks_raw_odoo_bin(tmp_path):
    mod = _module(tmp_path)
    d = hermes_adapter.pre_tool_call_directive("Bash", {"command": "python odoo-bin -i sale"}, mod)
    assert d is not None and d["decision"] == "block"


def test_pre_tool_call_allows_clean(tmp_path):
    mod = _module(tmp_path)
    assert hermes_adapter.pre_tool_call_directive("Bash", {"command": "ls"}, mod) is None


def test_pre_tool_call_blocks_multiedit_private_key(tmp_path):
    mod = _module(tmp_path)
    (mod / "models").mkdir()
    key = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"
    d = hermes_adapter.pre_tool_call_directive(
        "MultiEdit",
        {"file_path": str(mod / "models" / "m.py"),
         "edits": [{"old_string": "x", "new_string": key}]},
        mod,
    )
    assert d is not None and d["decision"] == "block"


def test_post_tool_call_notes_lint(tmp_path, monkeypatch):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "19")
    mod = _module(tmp_path)
    (mod / "views").mkdir()
    notes = hermes_adapter.post_tool_call_notes(
        "Write", {"file_path": str(mod / "views" / "v.xml"), "content": "<tree/>"}, mod)
    assert any("L1" in n for n in notes)


def test_command_gate_blocks_testing(tmp_path):
    mod = _module(tmp_path)
    msg = hermes_adapter.command_gate("testing", "/testing 19 mymod", mod)
    assert msg and "start-coding" in msg


def test_command_gate_blocks_testing_from_parent_dir(tmp_path):
    # gate invoked from the PARENT of mymod; module named in the args
    _module(tmp_path)
    msg = hermes_adapter.command_gate("testing", "19 mymod", tmp_path)
    assert msg and "start-coding" in msg


def test_command_gate_passes_plan_analysis(tmp_path):
    mod = _module(tmp_path)
    assert hermes_adapter.command_gate("plan-analysis", "/plan-analysis 19 mymod", mod) is None


def test_command_gate_passes_for_ready_gated_command(tmp_path):
    import json

    mod = _module(tmp_path)
    (mod / "docs" / "tasks.md").write_text("- [x] t1\n- [x] t2\n")
    (mod / "sessions").mkdir()
    (mod / "sessions" / "mymod_progress.json").write_text(json.dumps({"backend_tests_passed": True}))
    assert hermes_adapter.command_gate("testing", "/testing 19 mymod", mod) is None
