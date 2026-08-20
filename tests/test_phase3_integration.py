import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_controller_exposes_module_delegate():
    result = subprocess.run(
        [str(ROOT / "sandbox/bin/sandboxctl"), "--help"],
        capture_output=True, text=True, check=True,
    )
    assert "module" in result.stdout
    source = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert '"ODOO_EXECUTOR": "compose"' in source
    assert "MANAGE_MODULES" in source
    assert 'logs/odoo.log' in source


def test_compose_executor_emits_result_and_progress(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_DOCKER_LOG\"\n"
        "if [[ \"$*\" == *psql* ]] && [[ -f \"$FAKE_INSTALLED_FLAG\" ]]; then\n"
        "    echo 1\n"
        "fi\n"
        "if [[ \"$*\" == *'run --rm'* ]]; then\n"
        "    touch \"$FAKE_INSTALLED_FLAG\"\n"
        "fi\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    compose_file = tmp_path / "compose.yaml"
    env_file = tmp_path / "runtime.env"
    compose_file.write_text("services: {}\n")
    env_file.write_text("POSTGRES_USER=odoo_runtime\n")
    results = tmp_path / "results"
    logs = tmp_path / "logs"
    env = os.environ.copy()
    env.update({
        "PATH": f"{fake_bin}:{env['PATH']}", "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
        "FAKE_INSTALLED_FLAG": str(tmp_path / "installed.flag"),
        "ODOO_EXECUTOR": "compose", "ODOO_VERSION": "19", "ODOO_DB_NAME": "sandbox_db",
            "ODOO_EXEC_CONFIG_FILE": "/etc/odoo/odoo.conf", "ODOO_LOG_DIR": str(logs),
        "ODOO_RESULTS_DIR": str(results), "ODOO_PROGRESS_FILE": str(tmp_path / "progress.json"),
        "SESSION_ID": "19-fixture-test", "COMPOSE_FILE": str(compose_file),
        "COMPOSE_ENV_FILE": str(env_file), "POSTGRES_USER": "odoo_runtime",
    })
    proc = subprocess.run(
        ["bash", str(ROOT / "odoo_local_setup/manage_modules.sh"), "install", "sandbox_fixture"],
        env=env, cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    result_files = list(results.glob("install-*.json"))
    assert len(result_files) == 1
    data = json.loads(result_files[0].read_text())
    assert data["status"] == "succeeded"
    assert data["operation"] == "install"
    assert data["session_id"] == "19-fixture-test"
    progress = json.loads((tmp_path / "progress.json").read_text())
    assert progress["last_result"] == str(result_files[0])
    calls = (tmp_path / "docker.log").read_text()
    assert "stop odoo" in calls
    assert "run --rm -T odoo odoo" in calls
    assert "up -d --wait --wait-timeout 180 odoo" in calls


def test_compose_executor_fails_when_module_not_actually_installed(tmp_path):
    """Odoo's -i/-u CLI path skips an unresolvable dependency with only a
    warning and still exits 0; the operation result must not report
    'succeeded' unless the module actually reached ir_module_module.state
    == 'installed'. Simulates a module stuck at 'to install' (e.g. a
    missing Enterprise dependency) by having the fake psql check report
    not-installed."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_DOCKER_LOG\"\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    compose_file = tmp_path / "compose.yaml"
    env_file = tmp_path / "runtime.env"
    compose_file.write_text("services: {}\n")
    env_file.write_text("POSTGRES_USER=odoo_runtime\n")
    results = tmp_path / "results"
    logs = tmp_path / "logs"
    env = os.environ.copy()
    env.update({
        "PATH": f"{fake_bin}:{env['PATH']}", "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
        "ODOO_EXECUTOR": "compose", "ODOO_VERSION": "19", "ODOO_DB_NAME": "sandbox_db",
        "ODOO_EXEC_CONFIG_FILE": "/etc/odoo/odoo.conf", "ODOO_LOG_DIR": str(logs),
        "ODOO_RESULTS_DIR": str(results), "ODOO_PROGRESS_FILE": str(tmp_path / "progress.json"),
        "SESSION_ID": "19-fixture-test", "COMPOSE_FILE": str(compose_file),
        "COMPOSE_ENV_FILE": str(env_file), "POSTGRES_USER": "odoo_runtime",
    })
    proc = subprocess.run(
        ["bash", str(ROOT / "odoo_local_setup/manage_modules.sh"), "install", "account_report_template"],
        env=env, cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    result_files = list(results.glob("install-*.json"))
    assert len(result_files) == 1
    data = json.loads(result_files[0].read_text())
    assert data["status"] == "failed"
    assert data["error"]["code"] == "install_failed"


def test_session_start_prefers_manifest(tmp_path):
    session_dir = tmp_path / ".sandbox"
    session_dir.mkdir()
    (session_dir / "session.json").write_text(json.dumps({
        "session_id": "19-fixture-hook", "odoo_version": "19.0",
        "module": "sandbox_fixture", "status": "ready",
        "runtime": {"compose_project": "19-fixture-hook"},
    }))
    proc = subprocess.run(
        ["bash", str(ROOT / "plugin/hooks/session_start.sh")],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert "Sandbox session 19-fixture-hook" in proc.stdout
    assert "http://odoo:8069" in proc.stdout


def test_lifecycle_skills_use_controller_and_forbid_raw_odoo_bin():
    for relative in (
        "plugin/skills/CommandingSystem/start_coding_workflow.md",
        "plugin/skills/CommandingSystem/testing_workflow.md",
        "plugin/skills/Odoo_Custom_Backend_Testing/SKILL.md",
        "plugin/skills/Odoo_Custom_Frontend_Testing/SKILL.md",
    ):
        text = (ROOT / relative).read_text()
        assert "sandboxctl module" in text
        assert "Do not" in text and "odoo-bin" in text


def test_odoo_tools_skills_route_test_lifecycle_through_sandboxctl():
    """OdooTools17/18/19 mention raw odoo-bin for scaffold/shell (fine, those
    aren't lifecycle-gate operations), but the Tests bullet specifically must
    route through sandboxctl module ... test, not raw odoo-bin --test-tags,
    matching the sole-entrypoint rule audited for Phase 8."""
    for relative in (
        "plugin/skills/OdooTools17/SKILL.md",
        "plugin/skills/OdooTools18/SKILL.md",
        "plugin/skills/OdooTools19/SKILL.md",
    ):
        text = (ROOT / relative).read_text()
        assert "sandboxctl module" in text
        assert "never invoke raw" in text and "odoo-bin" in text
