import hashlib
import json
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_agent_neutral_kit_is_versioned_and_locked():
    spec = ROOT / "sandbox/kits/odoo-mixin/spec.yaml"
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    kit = lock["kits"]["odoo-mixin"]
    assert 'schemaVersion: "2"' in spec.read_text()
    assert "kind: mixin" in spec.read_text()
    assert f"version: {kit['version']}" in spec.read_text()
    assert hashlib.sha256(spec.read_bytes()).hexdigest() == kit["spec_sha256"]
    assert lock["sbx_version"] == "0.38.x"


def test_builtin_agents_share_one_runtime_adapter():
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    assert set(lock["agents"]) == {"codex", "claude", "copilot"}
    assert all(not entry["custom_template_required"] for entry in lock["agents"].values())
    launcher = (ROOT / "sandbox/bin/sandbox-agent").read_text()
    assert "codex|claude|copilot" in launcher
    assert "sandboxctl module" in launcher
    assert "--kit" in launcher and "--clone" in launcher


def test_launcher_and_artifact_validator_are_executable():
    for relative in ("sandbox/bin/sandbox-agent", "sandbox/scripts/validate-artifacts.sh"):
        assert (ROOT / relative).stat().st_mode & stat.S_IXUSR
    result = subprocess.run(
        [str(ROOT / "sandbox/scripts/validate-artifacts.sh")],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert "artifacts are pinned" in result.stdout


def test_adapter_does_not_accept_or_persist_secret_values():
    launcher = (ROOT / "sandbox/bin/sandbox-agent").read_text()
    assert "--token" not in launcher
    assert "API_KEY=" not in launcher
    docs = (ROOT / "docs/docker-sandbox/phase-4/agent-adapters.md").read_text()
    assert "sbx secret set openai --oauth" in docs
    assert "secret-bearing `.env`" in docs


def test_ide_tasks_delegate_to_launcher():
    tasks = json.loads((ROOT / ".vscode/tasks.json").read_text())
    commands = {task["command"] for task in tasks["tasks"]}
    assert commands == {"${workspaceFolder}/sandbox/bin/sandbox-agent"}
    labels = {task["label"] for task in tasks["tasks"]}
    assert labels == {"Odoo Sandbox: module test", "Odoo Sandbox: correlated Odoo logs"}
