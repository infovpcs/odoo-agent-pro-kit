"""Phase 9: run-mode executor for Docker Cloud Sandboxes.

Inside a Docker Cloud Sandbox, `docker exec` into a running container reaches neither the
container nor the VM filesystem, so exec-based health checks never pass and every
`compose exec` fails (reproduced 2026-09-25, see SESSION_CONTEXT.md "Phase 9 probe"). One-shot
containers work. SANDBOX_EXEC_MODE=run replaces every exec with `compose run --rm --no-deps`
and health-check waits with network probes from one-shot containers. The default mode
(`exec`) must stay byte-for-byte unchanged.
"""
import importlib.machinery
import importlib.util
import io
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "pg-secret-value"


def load_controller():
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader("sandboxctl_phase9", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def fake_session(controller, tmp_path, mode=None):
    controller.ROOT = tmp_path
    session = "cloud19"
    directory = controller.state_dir(session)
    for child in ("logs", "results", "diagnostics", "backups"):
        (directory / child).mkdir(parents=True, exist_ok=True)
    lines = ["COMPOSE_PROJECT_NAME=cloud19", "POSTGRES_USER=odoo_runtime",
             f"POSTGRES_PASSWORD={PASSWORD}", "ODOO_DB_NAME=sandbox_db"]
    if mode:
        lines.append(f"SANDBOX_EXEC_MODE={mode}")
    (directory / "runtime.env").write_text("\n".join(lines) + "\n")
    (directory / "session.json").write_text(
        '{"session_id": "cloud19", "odoo_version": "19.0", "module": "sandbox_fixture", "status": "ready"}')
    (directory / "events.jsonl").write_text("")
    return session


class Recorder:
    def __init__(self, returncode=0):
        self.calls = []
        self.returncode = returncode

    def __call__(self, command, *args, **kwargs):
        self.calls.append({"cmd": list(command), "env": kwargs.get("env") or {}, "kwargs": kwargs})
        return subprocess.CompletedProcess(command, self.returncode, stdout="", stderr="")

    def compose_args(self):
        """The part of each docker compose call after `-f <compose.yaml>`."""
        out = []
        for call in self.calls:
            cmd = call["cmd"]
            if cmd[:2] == ["docker", "compose"] and "-f" in cmd:
                out.append(" ".join(cmd[cmd.index("-f") + 2:]))
        return out


@pytest.fixture
def recorder(monkeypatch):
    def install(controller, returncode=0):
        rec = Recorder(returncode)
        monkeypatch.setattr(controller.subprocess, "run", rec)
        monkeypatch.setattr(controller.time, "sleep", lambda _s: None)
        return rec
    return install


# --- default exec mode is unchanged --------------------------------------------------

def test_exec_mode_is_the_default_and_passes_commands_through(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path)
    rec = recorder(controller)
    controller.compose(session, "up", "-d", "--wait", "--wait-timeout", "180", "db")
    controller.compose(session, "exec", "-T", "odoo", "python3", "-V")
    assert rec.compose_args() == ["up -d --wait --wait-timeout 180 db", "exec -T odoo python3 -V"]


def test_unknown_exec_mode_is_rejected(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="ssh")
    recorder(controller)
    with pytest.raises(RuntimeError, match="SANDBOX_EXEC_MODE"):
        controller.compose(session, "ps")


# --- run mode: compose() translation ---------------------------------------------------

def test_run_mode_up_wait_db_starts_without_deps_and_probes_over_the_network(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    rec = recorder(controller)
    controller.compose(session, "up", "-d", "--wait", "--wait-timeout", "180", "db")
    calls = rec.compose_args()
    assert calls[0] == "up -d --no-deps db"
    assert calls[1] == "run --rm --no-deps -T -e PGPASSWORD db pg_isready -h db -U odoo_runtime -d sandbox_db"
    assert not any(" exec " in f" {c} " or "--wait" in c for c in calls)
    probe = rec.calls[1]
    assert probe["env"]["PGPASSWORD"] == PASSWORD
    assert PASSWORD not in " ".join(probe["cmd"])


def test_run_mode_full_stack_up_is_sequential_db_then_odoo(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    rec = recorder(controller)
    controller.compose(session, "up", "-d", "--wait", "--wait-timeout", "180")
    calls = rec.compose_args()
    assert calls[0] == "up -d --no-deps db"
    assert calls[1].startswith("run --rm --no-deps -T -e PGPASSWORD db pg_isready -h db")
    assert calls[2] == "up -d --no-deps odoo"
    assert calls[3].startswith("run --rm --no-deps -T odoo python3 -c")
    assert "http://odoo:8069/web/health" in calls[3]


def test_run_mode_run_gets_no_deps_and_exec_becomes_a_one_shot_run(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    rec = recorder(controller)
    controller.compose(session, "run", "--rm", "odoo", "odoo", "--init", "base")
    controller.compose(session, "run", "--rm", "--no-deps", "-T", "odoo", "odoo", "shell")
    controller.compose(session, "exec", "-T", "odoo", "python3", "/workspace/scripts/fixture-lifecycle.py")
    assert rec.compose_args() == [
        "run --rm --no-deps odoo odoo --init base",
        "run --rm --no-deps -T odoo odoo shell",
        "run --rm --no-deps -T -e ODOO_URL=http://odoo:8069 odoo python3 /workspace/scripts/fixture-lifecycle.py",
    ]


def test_run_mode_readiness_times_out_with_a_clear_error(tmp_path, recorder, monkeypatch):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    recorder(controller)
    monkeypatch.setattr(controller, "_probe", lambda _session, _service: False)
    with pytest.raises(RuntimeError, match="not ready within 0s: db"):
        controller.compose(session, "up", "-d", "--wait", "--wait-timeout", "0", "db")


def test_run_mode_wait_ready_uses_network_probes_not_health_status(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    rec = recorder(controller)
    controller.wait_ready(session, timeout=5)
    calls = rec.compose_args()
    assert any("pg_isready -h db" in c for c in calls)
    assert any("http://odoo:8069/web/health" in c for c in calls)
    assert not any(c.startswith("ps") for c in calls)


# --- run mode: backup / restore --------------------------------------------------------

def test_run_mode_backup_uses_a_one_shot_client_with_password_in_env(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    rec = recorder(controller)
    controller.database_backup(session)
    dump = [c for c in rec.calls if "pg_dump" in c["cmd"]][0]
    args = " ".join(dump["cmd"][dump["cmd"].index("-f") + 2:])
    assert args == "run --rm --no-deps -T -e PGPASSWORD db pg_dump -Fc -h db -U odoo_runtime -d sandbox_db"
    assert dump["env"]["PGPASSWORD"] == PASSWORD
    assert PASSWORD not in " ".join(dump["cmd"])
    assert isinstance(dump["kwargs"].get("stdout"), io.IOBase)


def test_exec_mode_backup_is_unchanged(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path)
    rec = recorder(controller)
    controller.database_backup(session)
    dump = [c for c in rec.calls if "pg_dump" in c["cmd"]][0]
    args = " ".join(dump["cmd"][dump["cmd"].index("-f") + 2:])
    assert args == "exec -T db pg_dump -Fc -U odoo_runtime -d sandbox_db"


def test_run_mode_restore_uses_a_one_shot_client(tmp_path, recorder):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    backup = controller.state_dir(session) / "backups" / "cloud19-1.dump"
    backup.write_bytes(b"PGDMP")
    rec = recorder(controller)
    controller.database_restore(session, str(backup))
    restore = [c for c in rec.calls if "pg_restore" in c["cmd"]][0]
    args = " ".join(restore["cmd"][restore["cmd"].index("-f") + 2:])
    assert args == ("run --rm --no-deps -T -e PGPASSWORD db pg_restore --clean --if-exists --no-owner "
                    "-h db -U odoo_runtime -d sandbox_db")
    assert restore["env"]["PGPASSWORD"] == PASSWORD
    assert not any(" exec " in f" {c} " or "--wait" in c for c in rec.compose_args())


def test_create_records_the_exec_mode_in_runtime_env():
    source = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert '"SANDBOX_EXEC_MODE": runtime_exec_mode()' in source


def test_fixture_lifecycle_honours_odoo_url():
    source = (ROOT / "sandbox/scripts/fixture-lifecycle.py").read_text()
    assert 'os.environ.get("ODOO_URL", "http://127.0.0.1:8069")' in source


# --- manage_modules.sh compose executor in run mode ------------------------------------

def _run_manage_modules(tmp_path, mode):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s|PGPASSWORD=%s\\n' \"$*\" \"${PGPASSWORD:-}\" >> \"$FAKE_DOCKER_LOG\"\n"
        "if [[ \"$*\" == *psql* ]] && [[ -f \"$FAKE_INSTALLED_FLAG\" ]]; then echo 1; fi\n"
        "if [[ \"$*\" == *'odoo odoo --config'* ]]; then touch \"$FAKE_INSTALLED_FLAG\"; fi\n"
        "exit 0\n"
    )
    docker.chmod(0o755)
    compose_file = tmp_path / "compose.yaml"
    env_file = tmp_path / "runtime.env"
    compose_file.write_text("services: {}\n")
    env_file.write_text("POSTGRES_USER=odoo_runtime\n")
    env = os.environ.copy()
    env.update({
        "PATH": f"{fake_bin}:{env['PATH']}", "FAKE_DOCKER_LOG": str(tmp_path / "docker.log"),
        "FAKE_INSTALLED_FLAG": str(tmp_path / "installed.flag"),
        "ODOO_EXECUTOR": "compose", "ODOO_VERSION": "19", "ODOO_DB_NAME": "sandbox_db",
        "ODOO_EXEC_CONFIG_FILE": "/etc/odoo/odoo.conf", "ODOO_LOG_DIR": str(tmp_path / "logs"),
        "ODOO_RESULTS_DIR": str(tmp_path / "results"), "ODOO_PROGRESS_FILE": str(tmp_path / "progress.json"),
        "SESSION_ID": "cloud19", "COMPOSE_FILE": str(compose_file), "COMPOSE_ENV_FILE": str(env_file),
        "POSTGRES_USER": "odoo_runtime", "POSTGRES_PASSWORD": PASSWORD, "SANDBOX_EXEC_MODE": mode,
    })
    proc = subprocess.run(["bash", str(ROOT / "odoo_local_setup/manage_modules.sh"), "install", "sandbox_fixture"],
                          env=env, cwd=ROOT, capture_output=True, text=True)
    return proc, (tmp_path / "docker.log").read_text().splitlines()


def test_manage_modules_run_mode_never_execs_or_waits_on_health(tmp_path):
    proc, lines = _run_manage_modules(tmp_path, "run")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    calls = [ln.split("|")[0] for ln in lines]
    joined = "\n".join(calls)
    assert "run --rm --no-deps -T odoo odoo --config /etc/odoo/odoo.conf --database sandbox_db --init sandbox_fixture" in joined
    assert "up -d --no-deps odoo" in joined
    assert "http://odoo:8069/web/health" in joined
    psql = [ln for ln in lines if "psql" in ln]
    assert psql and all("run --rm --no-deps -T -e PGPASSWORD db psql -h db" in ln for ln in psql)
    assert all(ln.endswith(f"PGPASSWORD={PASSWORD}") for ln in psql)
    assert not any(" exec " in f" {c} " for c in calls)
    assert not any("--wait" in c for c in calls)


def test_manage_modules_exec_mode_is_unchanged(tmp_path):
    proc, lines = _run_manage_modules(tmp_path, "exec")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    joined = "\n".join(ln.split("|")[0] for ln in lines)
    assert "run --rm -T odoo odoo --config" in joined
    assert "up -d --wait --wait-timeout 180 odoo" in joined
    assert "exec -T db psql -U odoo_runtime" in joined


# --- odoo-mixin network allowlist ------------------------------------------------------

def test_mixin_allows_docker_hub_cloudfront_blob_host():
    # Docker Hub serves image blobs from production.cloudfront.docker.com; in a Cloud Sandbox
    # (default deny-all) the pinned odoo:19.0 pull failed "Forbidden" without it (2026-09-25).
    import json
    spec = (ROOT / "sandbox/kits/odoo-mixin/spec.yaml").read_text()
    for host in ("auth.docker.io", "registry-1.docker.io", "production.cloudflare.docker.com",
                 "production.cloudfront.docker.com"):
        assert f"- {host}\n" in spec, host
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    assert lock["kits"]["odoo-mixin"]["version"] == lock["release"] == "0.5.2"


def test_upgrade_rollback_derives_the_kit_version_from_the_lock():
    source = (ROOT / "sandbox/tests/upgrade-rollback.py").read_text()
    assert '"version: 0.5.1"' not in source


# --- sandbox/tests/lifecycle.sh in run mode --------------------------------------------

def _run_lifecycle(tmp_path, mode, versions=None):
    """Run a copy of lifecycle.sh inside a fake repo with fake `docker` and `sandboxctl`."""
    repo = tmp_path / "repo"
    (repo / "sandbox/tests").mkdir(parents=True)
    (repo / "sandbox/bin").mkdir(parents=True)
    (repo / "sandbox/compose").mkdir(parents=True)
    (repo / "sandbox/compose/compose.yaml").write_text("services: {}\n")
    script = repo / "sandbox/tests/lifecycle.sh"
    script.write_text((ROOT / "sandbox/tests/lifecycle.sh").read_text())
    log = tmp_path / "calls.log"
    ctl = repo / "sandbox/bin/sandboxctl"
    ctl.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'ctl %s\\n' \"$*\" >> \"$FAKE_LOG\"\n"
        "state=\"$(cd \"$(dirname \"$0\")/../..\" && pwd)/.sandbox/sessions\"\n"
        "case \"$1\" in\n"
        "  create) session=\"${@: -1}\"; mkdir -p \"$state/$session/addons/sandbox_fixture/data\"\n"
        "    printf 'SANDBOX_EXEC_MODE=%s\\n' \"${SANDBOX_EXEC_MODE:-exec}\" > \"$state/$session/runtime.env\"\n"
        "    echo '<field>installed</field>' > \"$state/$session/addons/sandbox_fixture/data/fixture_data.xml\" ;;\n"
        "  export) out=\"$state/$2/export.tgz\"; echo data > \"$out\"; echo \"$out\" ;;\n"
        "  destroy) rm -rf \"$state/$2\" ;;\n"
        "esac\n"
    )
    ctl.chmod(0o755)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text("#!/usr/bin/env bash\nprintf 'docker %s\\n' \"$*\" >> \"$FAKE_LOG\"\nexit 0\n")
    docker.chmod(0o755)
    env = os.environ.copy()
    env.update({"PATH": f"{fake_bin}:{env['PATH']}", "FAKE_LOG": str(log), "SANDBOX_EXEC_MODE": mode})
    if versions:
        env["SANDBOX_LIFECYCLE_VERSIONS"] = versions
    proc = subprocess.run(["bash", str(script)], env=env, cwd=repo, capture_output=True, text=True)
    return proc, log.read_text().splitlines(), repo


def test_lifecycle_run_mode_uses_no_deps_and_network_readiness(tmp_path):
    proc, lines, _repo = _run_lifecycle(tmp_path, "run", versions="19")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    compose = [ln for ln in lines if ln.startswith("docker compose")]
    runs = [ln for ln in compose if " run " in ln]
    assert len(runs) == 2 and all(" run --rm --no-deps odoo odoo --config" in ln for ln in runs)
    assert any("--init sandbox_fixture" in ln for ln in runs)
    assert any("--update sandbox_fixture" in ln for ln in runs)
    assert any(ln.endswith(" up -d --no-deps odoo") for ln in compose)
    assert not any(ln.endswith(" start odoo") for ln in compose)
    # The readiness probe runs in a one-shot container, so it must target ODOO_URL, not loopback.
    probe = [ln for ln in lines if ln.startswith("ctl exec") and "web/health" in ln]
    assert probe and all("ODOO_URL" in ln for ln in probe)
    assert any(ln.startswith("ctl exec 19-fixture-live -- python3 /workspace/scripts/fixture-lifecycle.py")
               for ln in lines)
    assert not any(ln.startswith("ctl create --version 17") for ln in lines)


def test_lifecycle_updates_the_fixture_marker_before_crud(tmp_path):
    # The live cloud run failed `lifecycle_marker == "updated"` because this step was skipped.
    proc, lines, repo = _run_lifecycle(tmp_path, "run", versions="19")
    assert proc.returncode == 0, proc.stderr[-2000:]
    update = next(i for i, ln in enumerate(lines) if "--update sandbox_fixture" in ln)
    crud = next(i for i, ln in enumerate(lines) if "fixture-lifecycle.py" in ln)
    assert update < crud


def test_lifecycle_exec_mode_is_unchanged(tmp_path):
    proc, lines, _repo = _run_lifecycle(tmp_path, "exec")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    compose = [ln for ln in lines if ln.startswith("docker compose")]
    assert any(ln.endswith(" start odoo") for ln in compose)
    assert all(" run --rm odoo odoo --config" in ln for ln in compose if " run " in ln)
    assert not any("--no-deps" in ln for ln in compose)
    for version in ("17", "18", "19"):
        assert any(ln.startswith(f"ctl create --version {version} ") for ln in lines), version


# --- sbx version contract ----------------------------------------------------------------

def test_lock_pins_local_and_cloud_sbx_separately():
    # Local KVM evidence (Phases 0-8) is 0.38.x; `--cloud` needs >= 0.45.1 (validated 0.45.1).
    import json
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    assert lock["sbx_version"] == "0.38.x"
    assert lock["sbx_cloud_version"] == "0.45.x"


def test_release_compare_reports_a_cloud_sbx_change(tmp_path):
    import json
    previous = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    previous["sbx_cloud_version"] = "0.44.x"
    old = tmp_path / "previous-artifacts.lock"
    old.write_text(json.dumps(previous))
    proc = subprocess.run(["python3", str(ROOT / "sandbox/scripts/release-acceptance.py"), "compare", str(old)],
                          capture_output=True, text=True, check=True)
    changes = json.loads(proc.stdout)["changes"]
    assert {"component": "sbx_cloud_version", "from": "0.44.x", "to": "0.45.x"} in changes


# --- status health in run mode -----------------------------------------------------------

class PsRecorder(Recorder):
    """`compose ps` returns fixed rows; one-shot probes succeed unless the service is listed as down."""

    def __init__(self, rows, down=()):
        super().__init__()
        self.rows, self.down = rows, set(down)

    def __call__(self, command, *args, **kwargs):
        super().__call__(command, *args, **kwargs)
        joined = " ".join(command)
        if " ps " in f" {joined} ":
            import json
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(self.rows), stderr="")
        failed = any(f"--no-deps -T -e PGPASSWORD {s} " in joined or f"--no-deps -T {s} python3" in joined
                     for s in self.down)
        return subprocess.CompletedProcess(command, 1 if failed else 0, stdout="", stderr="")


ROWS = [{"Service": "db", "State": "running", "Health": "unhealthy"},
        {"Service": "odoo", "State": "running", "Health": "starting"}]


def test_run_mode_status_reports_health_from_network_probes(tmp_path, monkeypatch):
    # Docker health checks exec into the container, which never works in cloud; status must not
    # report a permanently unhealthy session when both services answer over the network.
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    monkeypatch.setattr(controller.subprocess, "run", PsRecorder([dict(r) for r in ROWS]))
    rows = controller.service_rows(session)
    assert [(r["Service"], r["Health"], r["DockerHealth"]) for r in rows] == [
        ("db", "healthy", "unhealthy"), ("odoo", "healthy", "starting")]


def test_run_mode_status_reports_an_unanswering_service_as_unhealthy(tmp_path, monkeypatch):
    controller = load_controller()
    session = fake_session(controller, tmp_path, mode="run")
    monkeypatch.setattr(controller.subprocess, "run", PsRecorder([dict(r) for r in ROWS], down={"odoo"}))
    health = {r["Service"]: r["Health"] for r in controller.service_rows(session)}
    assert health == {"db": "healthy", "odoo": "unhealthy"}


def test_exec_mode_status_keeps_docker_health(tmp_path, monkeypatch):
    controller = load_controller()
    session = fake_session(controller, tmp_path)
    rec = PsRecorder([dict(r) for r in ROWS])
    monkeypatch.setattr(controller.subprocess, "run", rec)
    rows = controller.service_rows(session)
    assert [(r["Service"], r["Health"]) for r in rows] == [("db", "unhealthy"), ("odoo", "starting")]
    assert all("DockerHealth" not in r for r in rows)
    assert len(rec.calls) == 1


# --- sandbox/tests/phase6-proof.sh in run mode -------------------------------------------

def _run_phase6_proof(tmp_path, mode):
    repo = tmp_path / "repo"
    state = repo / ".sandbox/sessions/phase6-primary"
    (state / "logs").mkdir(parents=True)
    (state / "runtime.env").write_text(f"SANDBOX_EXEC_MODE={mode}\n" if mode else "")
    (repo / "sandbox/tests").mkdir(parents=True)
    (repo / "sandbox/bin").mkdir(parents=True)
    (repo / "sandbox/tests/phase6-proof.sh").write_text((ROOT / "sandbox/tests/phase6-proof.sh").read_text())
    log = tmp_path / "calls.log"
    ctl = repo / "sandbox/bin/sandboxctl"
    ctl.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'ctl %s\\n' \"$*\" >> \"$FAKE_LOG\"\n"
        "case \"$1\" in\n"
        "  backup) echo /tmp/fake.dump ;;\n"
        "  diagnose) echo '{}' > \"${SANDBOX_OTEL_LOG_ENDPOINT#file://}\"; echo bundle.tgz ;;\n"
        "  logs) echo '[phase6-primary/19.0/sandbox_fixture/odoo] started' ;;\n"
        "esac\n")
    ctl.chmod(0o755)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text("#!/usr/bin/env bash\nprintf 'docker %s|SQL=%s\\n' \"$*\" \"${PHASE6_SQL:-}\" >> \"$FAKE_LOG\"\n"
                      "case \"$*\" in *PHASE6_SQL=SELECT*) echo 1 ;; esac\nexit 0\n")
    docker.chmod(0o755)
    env = os.environ.copy()
    env.update({"PATH": f"{fake_bin}:{env['PATH']}", "FAKE_LOG": str(log)})
    proc = subprocess.run(["bash", "sandbox/tests/phase6-proof.sh"], env=env, cwd=repo, capture_output=True, text=True)
    return proc, log.read_text().splitlines()


def test_phase6_proof_run_mode_uses_one_shot_psql_clients(tmp_path):
    proc, lines = _run_phase6_proof(tmp_path, "run")
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    compose = [ln for ln in lines if ln.startswith("docker compose")]
    assert len(compose) == 3
    assert all(" run --rm --no-deps -T " in ln and "psql -h db" in ln for ln in compose)
    assert not any(" exec " in ln for ln in compose)
    assert "BACKUP_RESTORE=passed" in proc.stdout


def test_phase6_proof_exec_mode_still_execs_into_db(tmp_path):
    proc, lines = _run_phase6_proof(tmp_path, None)
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    compose = [ln for ln in lines if ln.startswith("docker compose")]
    assert len(compose) == 3 and all(" exec -T " in ln and " db " in ln for ln in compose)
