"""Phase 10 (Phase 9 carry-over): /fleet allocation in Docker Cloud Sandboxes, internal-only."""
import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_fleet():
    loader = importlib.machinery.SourceFileLoader("sandbox_fleet_cloud", str(ROOT / "sandbox/bin/sandbox-fleet"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout.strip()


@pytest.fixture
def fleet(monkeypatch, tmp_path):
    module = load_fleet()
    monkeypatch.setattr(module, "STATE", tmp_path / "fleet")
    monkeypatch.setattr(module, "SESSIONS", tmp_path / "fleet/sessions")
    monkeypatch.setattr(module, "LOCK", tmp_path / "fleet/controller.lock")
    return module


def test_cloud_policy_names_a_billable_shape_and_ttl():
    config = json.loads((ROOT / "sandbox/config/concurrency.json").read_text())
    cloud = config["cloud"]
    assert (cloud["cpus"], cloud["memory_gib"]) == (4, 8)
    assert cloud["ttl_minutes"] == 120 and cloud["platform"] == "linux/amd64"
    assert cloud["exposure"] == "internal"


def test_cloud_shape_accepts_only_billable_sizes(fleet):
    assert fleet.cloud_shape(4, 8) == "medium"
    assert fleet.cloud_shape(8, 16) == "large"
    with pytest.raises(RuntimeError):
        fleet.cloud_shape(2, 8)


def test_sbx_command_honours_the_client_override(fleet, monkeypatch):
    monkeypatch.setenv("SANDBOX_SBX", "/opt/sbx-wrapper --flag")
    assert fleet.sbx("ls", cloud=True) == ["/opt/sbx-wrapper", "--flag", "--cloud", "ls"]
    monkeypatch.delenv("SANDBOX_SBX")
    assert fleet.sbx("ls") == ["sbx", "ls"]


def test_cli_accepts_cloud_and_rejects_copilot_in_cloud(fleet):
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "sandbox_fixture", "--cloud"])
    assert args.cloud is True
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "sandbox_fixture", "--cloud", "--agent", "copilot"])
    with pytest.raises(RuntimeError, match="cloud"):
        fleet.cmd_create(args)


def test_snapshot_captures_the_worktree_without_touching_index_or_refs(fleet, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / ".gitignore").write_text("ignored.txt\n")
    (repo / "tracked.txt").write_text("v1\n")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "base")
    head = git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").write_text("v2\n")
    (repo / "new.txt").write_text("untracked\n")
    (repo / "ignored.txt").write_text("secret\n")
    refs_before = git(repo, "for-each-ref")
    status_before = git(repo, "status", "--porcelain")
    commit = fleet.worktree_snapshot(repo)
    assert git(repo, "rev-parse", f"{commit}^") == head
    assert git(repo, "show", f"{commit}:tracked.txt") == "v2"
    assert git(repo, "show", f"{commit}:new.txt") == "untracked"
    assert "ignored.txt" not in git(repo, "ls-tree", "--name-only", commit)
    bundle = tmp_path / "s.bundle"
    fleet.write_bundle(repo, commit, bundle)
    assert git(repo, "for-each-ref") == refs_before
    assert git(repo, "status", "--porcelain") == status_before
    clone = tmp_path / "clone"
    subprocess.run(["git", "init", "-q", str(clone)], check=True)
    git(clone, "fetch", "-q", str(bundle), "refs/sandbox-fleet/*:refs/sandbox-fleet/*")
    git(clone, "checkout", "-q", "-b", "sandbox/x", commit)
    assert (clone / "new.txt").read_text() == "untracked\n"


def test_cloud_create_is_internal_only_and_runs_inner_controller_in_run_mode(fleet, monkeypatch):
    calls, scripts = [], []

    class Done:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(fleet, "run", lambda command, **kwargs: calls.append(command) or Done())
    monkeypatch.setattr(fleet, "worktree_snapshot", lambda repo: "c0ffee" * 6 + "abcd")
    monkeypatch.setattr(fleet, "write_bundle", lambda repo, commit, path: None)
    monkeypatch.setattr(fleet, "cloud_exec", lambda name, script, label, timeout: scripts.append((label, script)) or (0, "ok"))
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "sandbox_fixture", "--cloud"])
    fleet.cmd_create(args)
    create = next(c for c in calls if "create" in c)
    assert create[:3] == ["sbx", "--cloud", "create"]
    for flag, value in (("--cpus", "4"), ("--memory", "8g"), ("--platform", "linux/amd64"), ("--ttl", "120m"), ("--kit", "sandbox/kits/odoo-mixin")):
        assert create[create.index(flag) + 1] == value
    assert create[-1] == "codex"
    assert not any("ports" in c for c in calls), "internal-only: no port may be published"
    assert any(c[:3] == ["sbx", "--cloud", "cp"] for c in calls)
    label, script = scripts[0]
    assert label == "create"
    assert "git fetch -q /tmp/kit.bundle 'refs/sandbox-fleet/*:refs/sandbox-fleet/*'" in script
    assert "git checkout -q -b sandbox/odoo-20-sandbox-fixture-" in script
    assert "SANDBOX_EXEC_MODE=run" in script and "sandbox/bin/sandboxctl create --version 20 --module sandbox_fixture" in script
    session = fleet.read_sessions()[0]
    assert session["status"] == "ready" and session["ports"] == []
    assert session["runtime"] == {"mode": "cloud", "shape": "medium", "exposure": "internal", "snapshot": "c0ffee" * 6 + "abcd", "ttl_minutes": 120}


def test_cloud_create_failure_removes_the_cloud_sandbox(fleet, monkeypatch):
    calls = []

    class Done:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(fleet, "run", lambda command, **kwargs: calls.append(command) or Done())
    monkeypatch.setattr(fleet, "worktree_snapshot", lambda repo: "a" * 40)
    monkeypatch.setattr(fleet, "write_bundle", lambda repo, commit, path: None)
    monkeypatch.setattr(fleet, "cloud_exec", lambda name, script, label, timeout: (1, "boom"))
    args = fleet.parser().parse_args(["create", "--version", "19", "--module", "sandbox_fixture", "--cloud"])
    with pytest.raises(RuntimeError):
        fleet.cmd_create(args)
    assert calls[-1][:5] == ["sbx", "--cloud", "rm", "--force", calls[-1][4]]
    session = fleet.read_sessions()[0]
    assert session["status"] == "failed" and session["cleanup"]["outer_removed"] is True


def test_cloud_run_and_destroy_use_the_cloud_client(fleet, monkeypatch):
    calls, scripts = [], []

    class Done:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(fleet, "run", lambda command, **kwargs: calls.append(command) or Done())
    monkeypatch.setattr(fleet, "cloud_exec", lambda name, script, label, timeout: scripts.append(script) or (0, "ok"))
    fleet.write_session({"session_id": "odoo-20-m-abc123", "status": "ready", "runtime": {"mode": "cloud"},
                         "cleanup_guard": {"commit": False, "push": False, "patch_export": True}, "last_activity_at": fleet.now()})
    fleet.cmd_run(fleet.parser().parse_args(["run", "odoo-20-m-abc123", "test", "sandbox_fixture"]))
    assert "sandbox/bin/sandboxctl module odoo-20-m-abc123 test sandbox_fixture" in scripts[-1]
    fleet.cmd_destroy(fleet.parser().parse_args(["destroy", "odoo-20-m-abc123"]))
    assert "sandbox/bin/sandboxctl destroy odoo-20-m-abc123 --allow-unexported" in scripts[-1]
    assert calls[-1] == ["sbx", "--cloud", "rm", "--force", "odoo-20-m-abc123"]
    assert fleet.read_sessions()[0]["status"] == "destroyed"


def test_fleet_command_doc_states_cloud_is_internal_only():
    doc = (ROOT / "plugin/commands/fleet.md").read_text()
    assert "--cloud" in doc and "internal-only" in doc


# Phase 11: a cloud fleet session can import a private module group plus its requirements.
def _staging(tmp_path):
    tree = tmp_path / "staging"
    (tree / "mod_a").mkdir(parents=True)
    (tree / "mod_a/__manifest__.py").write_text("{'name': 'a', 'depends': ['base']}")
    (tree / "migration-report.json").write_text("{}")
    req_a, req_b = tmp_path / "a.txt", tmp_path / "b.txt"
    req_a.write_text("openai>=1\n"); req_b.write_text("httpx>=0.24\n")
    return tree, req_a, req_b


def test_cli_accepts_import_and_repeated_requirements(fleet, tmp_path):
    tree, req_a, req_b = _staging(tmp_path)
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "mod_a", "--cloud", "--import", str(tree),
                                      "--requirements", str(req_a), "--requirements", str(req_b)])
    assert args.import_source == str(tree) and args.requirements == [str(req_a), str(req_b)]


def test_import_is_cloud_only(fleet, tmp_path):
    tree, _, _ = _staging(tmp_path)
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "mod_a", "--import", str(tree)])
    with pytest.raises(RuntimeError, match="--cloud"):
        fleet.cmd_create(args)


def test_import_payload_holds_the_tree_and_requirements_but_no_git_or_secrets(fleet, tmp_path):
    import tarfile
    tree, req_a, req_b = _staging(tmp_path)
    (tree / ".git").mkdir(); (tree / ".git/config").write_text("x")
    (tree / ".env").write_text("SECRET=1")
    payload = fleet.import_payload("s1", str(tree), [str(req_a), str(req_b)])
    assert payload.is_relative_to(fleet.STATE)
    with tarfile.open(payload) as archive:
        names = sorted(archive.getnames())
    assert "tree/mod_a/__manifest__.py" in names and "requirements/0.txt" in names and "requirements/1.txt" in names
    assert not any(".git" in n.split("/") or n.endswith(".env") for n in names)


def test_import_payload_refuses_a_missing_tree(fleet, tmp_path):
    with pytest.raises(RuntimeError, match="import"):
        fleet.import_payload("s1", str(tmp_path / "missing"), [])


def test_cloud_create_with_import_ships_the_payload_and_passes_it_to_sandboxctl(fleet, monkeypatch, tmp_path):
    tree, req_a, req_b = _staging(tmp_path)
    calls, scripts = [], []

    class Done:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(fleet, "ROOT", tmp_path)
    monkeypatch.setattr(fleet, "BUNDLES", tmp_path / "fleet/bundles")
    monkeypatch.setattr(fleet, "run", lambda command, **kwargs: calls.append(command) or Done())
    monkeypatch.setattr(fleet, "worktree_snapshot", lambda repo: "b" * 40)
    monkeypatch.setattr(fleet, "write_bundle", lambda repo, commit, path: None)
    monkeypatch.setattr(fleet, "cloud_exec", lambda name, script, label, timeout: scripts.append((label, script)) or (0, "ok"))
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "mod_a", "--cloud", "--import", str(tree),
                                      "--requirements", str(req_a), "--requirements", str(req_b)])
    fleet.cmd_create(args)
    copies = [c for c in calls if c[:3] == ["sbx", "--cloud", "cp"]]
    assert any(c[-1].endswith(":/tmp/import.tgz") for c in copies)
    _, script = scripts[0]
    assert "tar -xzf /tmp/import.tgz -C ~/import" in script
    assert ("sandbox/bin/sandboxctl create --version 20 --module mod_a --session " in script
            and "--import ~/import/tree --requirements ~/import/requirements/0.txt --requirements ~/import/requirements/1.txt" in script)
