# tests/hooks/test_dispatcher.py
from __future__ import annotations
import json
import importlib.util
import os
import subprocess
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


def _real_git_module(tmp_path):
    """A real git repo with a module tree so Stop's stamp check has git-tracked files."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
                   cwd=tmp_path, check=True)
    return mod


def test_stop_no_reminder_when_stamp_absent(tmp_path, capsys):
    mod = _real_git_module(tmp_path)
    assert _run("Stop", {"cwd": str(mod)}) == 0
    assert capsys.readouterr().out == ""


def test_stop_reminds_when_stamp_stale(tmp_path, capsys):
    mod = _real_git_module(tmp_path)
    stamp = tmp_path / ".git" / "odoo-kit-validate.stamp"
    stamp.write_text("x")
    os.utime(stamp, (1, 1))  # ancient
    (mod / "docs" / "tasks.md").write_text("- [ ] t1\n- [ ] t2\n")  # tracked file now newer
    rc = _run("Stop", {"cwd": str(mod)})
    assert rc == 0
    assert "validate.sh" in capsys.readouterr().out


def test_bad_json_fails_open():
    assert odoo_hook.main(["PreToolUse"], "not json{") == 0


def test_unknown_event_fails_open(tmp_path):
    assert _run("Nonsense", {"cwd": str(tmp_path)}) == 0


def test_block_reason_goes_to_stderr(tmp_path, capsys):
    mod = _module(tmp_path)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "python3 odoo-bin -d x -i sale"}})
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.err.strip() != ""
    assert captured.out == ""


def test_warn_lint_goes_to_stdout_not_block(tmp_path, monkeypatch, capsys):
    # L2 (attrs=) is warn-severity on 18 -> stdout, rc 0. (<tree> is block on 18.)
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "18")
    mod = _module(tmp_path)
    rc = _run("PostToolUse", {"cwd": str(mod), "tool_name": "Write",
                              "tool_input": {"file_path": str(mod / "views" / "v.xml"),
                                             "content": '<odoo><field name="x" attrs="{}"/></odoo>'}})
    captured = capsys.readouterr()
    assert rc == 0
    assert "L2" in captured.out
    assert captured.err == ""


def test_posttooluse_blocks_tree_on_18(tmp_path, monkeypatch):
    # Recent Odoo 18 builds removed <tree> entirely -> block, not warn.
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "18")
    mod = _module(tmp_path)
    rc = _run("PostToolUse", {"cwd": str(mod), "tool_name": "Write",
                              "tool_input": {"file_path": str(mod / "views" / "v.xml"),
                                             "content": "<odoo><tree/></odoo>"}})
    assert rc == 2


def test_userpromptsubmit_gates_module_named_in_arg_from_parent(tmp_path):
    # /testing run from the PARENT of mymod, module named explicitly -> still gated
    mod = _module(tmp_path)
    del mod
    rc = _run("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "/testing 19 mymod"})
    assert rc == 2


def test_check_exception_fails_open(tmp_path, monkeypatch):
    mod = _module(tmp_path)

    def _boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(odoo_hook.guard, "classify_bash", _boom)
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "git push origin main"}})
    assert rc == 0


def test_hooks_disabled_is_noop(tmp_path, monkeypatch):
    mod = _module(tmp_path)
    monkeypatch.setenv("ODOO_KIT_HOOKS_DISABLED", "1")
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "Bash",
                             "tool_input": {"command": "python3 odoo-bin -i sale"}})
    assert rc == 0


def test_session_end_pid_cleanup():
    repo = Path(__file__).resolve().parents[2]
    pid_file = repo / "plugin" / "odoo_mcp" / "mcp_server_test.pid"
    pid_file.write_text("999999\n")
    try:
        rc = odoo_hook.main(["SessionEnd"], json.dumps({"cwd": str(repo)}))
        assert rc == 0
        assert not pid_file.exists()
    finally:
        if pid_file.exists():
            pid_file.unlink()


def test_multiedit_body_is_scanned(tmp_path):
    mod = _module(tmp_path)
    (mod / "models").mkdir()
    key = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----"
    rc = _run("PreToolUse", {"cwd": str(mod), "tool_name": "MultiEdit",
                             "tool_input": {"file_path": str(mod / "models" / "m.py"),
                                            "edits": [{"old_string": "x", "new_string": key}]}})
    assert rc == 2
