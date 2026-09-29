"""Phase 12 (finding 7): replay a session's recorded requirements freeze as pinned pip constraints."""
import importlib.machinery
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE_19 = "odoo@sha256:" + "a" * 64
BASE_20 = "odoo@sha256:" + "b" * 64


def load_controller():
    loader = importlib.machinery.SourceFileLoader("sandboxctl", str(ROOT / "sandbox/bin/sandboxctl"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_recorded_freeze_carries_odoo_version_and_base_image():
    controller = load_controller()
    text = controller.freeze_record("19.0", BASE_19, "click==8.5.0\nnltk==3.10.3\n")
    assert text.splitlines()[0] == f"# sandbox-requirements-freeze odoo_version=19.0 base_image={BASE_19}"
    assert text.splitlines()[1:] == ["click==8.5.0", "nltk==3.10.3"]


def test_replayed_freeze_returns_its_pins():
    controller = load_controller()
    text = controller.freeze_record("19.0", BASE_19, "click==8.5.0\nNLTK==3.10.3\n")
    assert controller.parse_freeze(text, "19.0", BASE_19) == ["click==8.5.0", "NLTK==3.10.3"]


def test_freeze_for_another_odoo_version_is_refused():
    controller = load_controller()
    text = controller.freeze_record("19.0", BASE_19, "click==8.5.0\n")
    with pytest.raises(SystemExit) as error:
        controller.parse_freeze(text, "20.0", BASE_19)
    assert "19.0" in str(error.value) and "20.0" in str(error.value)


def test_freeze_for_another_base_image_is_refused():
    controller = load_controller()
    text = controller.freeze_record("20.0", BASE_19, "click==8.5.0\n")
    with pytest.raises(SystemExit) as error:
        controller.parse_freeze(text, "20.0", BASE_20)
    assert "base image" in str(error.value)


def test_freeze_without_provenance_header_is_refused():
    controller = load_controller()
    with pytest.raises(SystemExit) as error:
        controller.parse_freeze("click==8.5.0\n", "19.0", BASE_19)
    assert "header" in str(error.value)


@pytest.mark.parametrize("line", ["click>=8", "-e git+https://x/y.git#egg=y", "pkg @ file:///tmp/pkg", "--index-url https://evil"])
def test_freeze_accepts_only_exact_pins(line):
    controller = load_controller()
    text = controller.freeze_record("19.0", BASE_19, line + "\n")
    with pytest.raises(SystemExit):
        controller.parse_freeze(text, "19.0", BASE_19)


def test_constraints_change_the_requirements_image_tag():
    controller = load_controller()
    base = "odoo-agent-dev:19-94a4f480b803"
    lines = ["nltk>=3.9.2"]
    assert controller.requirements_image(base, lines) == controller.requirements_image(base, lines, [])
    assert controller.requirements_image(base, lines, ["click==8.5.0"]) != controller.requirements_image(base, lines)


def test_create_cli_accepts_a_requirements_freeze():
    parser = load_controller().build_parser()
    args = parser.parse_args(["create", "--version", "19", "--module", "m", "--requirements", "a.txt",
                              "--requirements-freeze", "results/requirements-freeze.txt"])
    assert args.requirements_freeze == "results/requirements-freeze.txt"


def test_create_refuses_a_freeze_without_requirements(tmp_path):
    freeze = tmp_path / "freeze.txt"
    freeze.write_text(load_controller().freeze_record("19.0", BASE_19, "click==8.5.0\n"))
    result = subprocess.run([str(ROOT / "sandbox/bin/sandboxctl"), "create", "--version", "19", "--module", "sandbox_smoke",
                             "--session", "p12-freeze-only", "--requirements-freeze", str(freeze)],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "--requirements-freeze needs --requirements" in result.stderr
    assert not (ROOT / ".sandbox/sessions/p12-freeze-only").exists()


def test_requirements_dockerfile_applies_constraints_and_tolerates_a_slow_index():
    dockerfile = (ROOT / "sandbox/images/odoo-dev/requirements.Dockerfile").read_text()
    assert "COPY requirements.txt constraints.txt /tmp/" in dockerfile
    assert "-r /tmp/sandbox-requirements.txt -c /tmp/sandbox-constraints.txt" in dockerfile
    # Finding 7's ResolutionImpossible came from PyPI read timeouts (pip's default 15 s, 5 retries).
    assert "ARG PIP_DEFAULT_TIMEOUT=60" in dockerfile and "ARG PIP_RETRIES=10" in dockerfile
    assert dockerfile.index("ARG PIP_RETRIES") < dockerfile.index("pip install")


def test_create_records_the_freeze_with_provenance():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    build = controller[controller.index("def build_requirements_image"):controller.index("def prepare_import")]
    assert "freeze_record(" in build and "requirements-freeze.txt" in build


# The cloud fleet ships the freeze with the import payload and replays it in the sandbox.
def load_fleet():
    loader = importlib.machinery.SourceFileLoader("sandbox_fleet_p12", str(ROOT / "sandbox/bin/sandbox-fleet"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_fleet_payload_carries_the_freeze(tmp_path, monkeypatch):
    import tarfile
    fleet = load_fleet()
    monkeypatch.setattr(fleet, "STATE", tmp_path / "state")
    (tmp_path / "tree/mod_a").mkdir(parents=True)
    (tmp_path / "tree/mod_a/__manifest__.py").write_text("{}")
    req, freeze = tmp_path / "r.txt", tmp_path / "f.txt"
    req.write_text("nltk>=3.9.2\n"); freeze.write_text("# header\nclick==8.5.0\n")
    payload = fleet.import_payload("s1", str(tmp_path / "tree"), [str(req)], str(freeze))
    with tarfile.open(payload) as archive:
        assert "requirements/freeze.txt" in archive.getnames()


def test_fleet_create_passes_the_freeze_to_sandboxctl(tmp_path, monkeypatch):
    fleet = load_fleet()
    (tmp_path / "tree/mod_a").mkdir(parents=True)
    (tmp_path / "tree/mod_a/__manifest__.py").write_text("{}")
    req, freeze = tmp_path / "r.txt", tmp_path / "f.txt"
    req.write_text("nltk>=3.9.2\n"); freeze.write_text("# header\nclick==8.5.0\n")
    scripts = []

    class Done:
        returncode, stdout, stderr = 0, "", ""

    monkeypatch.setattr(fleet, "ROOT", tmp_path)
    # Every module-level path under .sandbox/fleet must point at tmp_path: a clean checkout has no
    # .sandbox/fleet, and the real one must not collect fake session records.
    monkeypatch.setattr(fleet, "STATE", tmp_path / "fleet")
    monkeypatch.setattr(fleet, "SESSIONS", tmp_path / "fleet/sessions")
    monkeypatch.setattr(fleet, "LOCK", tmp_path / "fleet/controller.lock")
    monkeypatch.setattr(fleet, "BUNDLES", tmp_path / "fleet/bundles")
    monkeypatch.setattr(fleet, "run", lambda command, **kwargs: Done())
    monkeypatch.setattr(fleet, "worktree_snapshot", lambda repo: "b" * 40)
    monkeypatch.setattr(fleet, "write_bundle", lambda repo, commit, path: None)
    monkeypatch.setattr(fleet, "cloud_exec", lambda name, script, label, timeout: scripts.append(script) or (0, "ok"))
    args = fleet.parser().parse_args(["create", "--version", "20", "--module", "mod_a", "--cloud", "--import", str(tmp_path / "tree"),
                                      "--requirements", str(req), "--requirements-freeze", str(freeze)])
    fleet.cmd_create(args)
    assert "--requirements ~/import/requirements/0.txt --requirements-freeze ~/import/requirements/freeze.txt" in scripts[0]
