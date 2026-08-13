import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_contract_verifier_passes():
    proc = subprocess.run(
        ["python3", "sandbox/scripts/release-acceptance.py", "verify"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "are pinned" in proc.stdout


def test_upgrade_rollback_contract_passes():
    proc = subprocess.run(
        ["python3", "sandbox/tests/upgrade-rollback.py"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "byte-identical rollback passed" in proc.stdout


def test_dependency_inventory_is_machine_readable():
    (ROOT / ".sandbox").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / ".sandbox") as directory:
        relative = str(Path(directory).relative_to(ROOT) / "inventory.json")
        subprocess.run(
            ["python3", "sandbox/scripts/dependency-inventory.py", "--output", relative],
            cwd=ROOT, check=True,
        )
        report = json.loads((ROOT / relative).read_text())
        assert report["project_license"] == "Apache-2.0"
        assert len(report["container_images"]) == 4
        assert all("@sha256:" in value for value in report["container_images"].values())


def test_phase7_skill_and_runbooks_are_discoverable():
    skill = (ROOT / "plugin/skills/DockerSandboxOperations/SKILL.md").read_text()
    assert "migrate-local.py" in skill
    assert "release-acceptance.py verify" in skill
    for name in ("operator-runbooks.md", "release-acceptance.md", "migration-capacity.md"):
        assert (ROOT / "docs/docker-sandbox/phase-7" / name).is_file()


def test_migration_rejects_invalid_module_name(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    proc = subprocess.run(
        ["python3", "sandbox/scripts/migrate-local.py", "--source", str(source),
         "--version", "19", "--name", "../../escaped"],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode != 0
    assert "valid Odoo technical module name" in proc.stderr
    assert not (tmp_path / "escaped").exists()


def test_migration_rejects_name_that_breaks_generated_session_id(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=source, check=True)
    proc = subprocess.run(
        ["python3", "sandbox/scripts/migrate-local.py", "--source", str(source),
         "--version", "19", "--name", "a" * 53],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode != 0
    assert "at most 52 characters" in proc.stderr
