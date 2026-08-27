from __future__ import annotations
import json, importlib.util, os, subprocess, time
from pathlib import Path

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "contributor_hook.py"
_spec = importlib.util.spec_from_file_location("contributor_hook", _MOD)
contributor_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contributor_hook)


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
                   cwd=tmp_path, check=True)
    return tmp_path


def _commit_tracked_change(tmp_path, name="b.py"):
    (tmp_path / name).write_text("y = 2\n")
    subprocess.run(["git", "add", name], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "change"],
                   cwd=tmp_path, check=True)


def _run(event, payload):
    return contributor_hook.main([event], json.dumps(payload))


def test_git_push_blocked_without_authz(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    assert _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                               "tool_input": {"command": "git push origin main"}}) == 2


def test_git_push_allowed_with_authz(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.setenv("AGENTS_PHASE_AUTHORIZED", "1")
    assert _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                               "tool_input": {"command": "git push origin main"}}) == 0


def test_commit_blocked_when_validate_stale(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    stamp = repo / ".git" / "odoo-kit-validate.stamp"
    stamp.write_text("x")
    os.utime(stamp, (1, 1))  # ancient stamp
    _commit_tracked_change(repo)  # tracked file mtime now >> stamp mtime
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m wip"}})
    assert rc == 2


def test_commit_allowed_when_no_stamp(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    _commit_tracked_change(repo)
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m wip"}})
    assert rc == 0


def test_commit_allowed_untracked_only(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    stamp = repo / ".git" / "odoo-kit-validate.stamp"
    stamp.write_text("ok\n")
    os.utime(stamp, None)  # stamp = now
    time.sleep(0.01)
    (repo / "untracked.py").write_text("z = 3\n")  # NOT git add-ed
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m done"}})
    assert rc == 0


def test_commit_ok_when_stamp_fresh(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    stamp = repo / ".git" / "odoo-kit-validate.stamp"
    time.sleep(0.01)
    stamp.write_text("ok\n")
    rc = _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                             "tool_input": {"command": "git commit -m done"}})
    assert rc == 0


def test_bad_json_fails_open():
    assert contributor_hook.main(["PreToolUse"], "{bad") == 0


def test_disabled_env_is_noop(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.delenv("AGENTS_PHASE_AUTHORIZED", raising=False)
    monkeypatch.setenv("ODOO_KIT_HOOKS_DISABLED", "1")
    assert _run("PreToolUse", {"cwd": str(repo), "tool_name": "Bash",
                               "tool_input": {"command": "git push origin main"}}) == 0


def test_session_start_prints_next_phase(tmp_path, capsys):
    repo = _git_repo(tmp_path)
    tasks = repo / "docs" / "docker-sandbox" / "tasks.md"
    tasks.parent.mkdir(parents=True, exist_ok=True)
    tasks.write_text("- [x] done\n- [ ] Phase 9: do the thing\n- [ ] Phase 10: later\n")
    rc = _run("SessionStart", {"cwd": str(repo)})
    out = capsys.readouterr().out
    assert rc == 0
    assert "Phase 9: do the thing" in out
