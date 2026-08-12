import json
import os
import stat
import subprocess
import importlib.machinery
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader("sandboxctl", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_runtime_files_are_present_and_pinned():
    lock = (ROOT / "sandbox/config/images.lock").read_text()
    assert "odoo:19.0@sha256:" in lock
    assert "postgres:15-bookworm@sha256:" in lock
    assert lock.count("@sha256:") == 2
    compose = (ROOT / "sandbox/compose/compose.yaml").read_text()
    assert "condition: service_healthy" in compose
    assert "db-data:" in compose
    assert "filestore:" in compose
    assert "cache:" in compose


def test_controller_help_and_executable_mode():
    controller = ROOT / "sandbox/bin/sandboxctl"
    assert controller.stat().st_mode & stat.S_IXUSR
    result = subprocess.run([str(controller), "--help"], capture_output=True, text=True, check=True)
    for command in ("create", "status", "exec", "logs", "stop", "start", "destroy"):
        assert command in result.stdout


def test_create_initializes_the_odoo_schema_before_readiness():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    initialize = controller.index('"--init", "base"')
    start_stack = controller.index('compose(session, "up", "-d", "--wait", "--wait-timeout", str(args.timeout))', initialize)
    assert initialize < start_stack


def test_generated_config_is_readable_by_non_root_linux_container():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert "os.chmod(config_file, 0o644)" in controller
    assert 'os.chmod(directory / "runtime.env", 0o600)' in controller
    assert 'os.chmod(directory / "logs", 0o777)' in controller
    assert 'os.chmod(directory / "results", 0o777)' in controller


def test_fixture_manifest_is_valid_json_like_python():
    manifest = (ROOT / "sandbox/fixtures/sandbox_fixture/__manifest__.py").read_text()
    assert '"version": "19.0.1.0.0"' in manifest
    assert '"license": "LGPL-3"' in manifest


def test_operation_schema_covers_controller_operations():
    schema = json.loads((ROOT / "sandbox/schemas/operation-result.schema.json").read_text())
    operations = set(schema["properties"]["operation"]["enum"])
    assert {"create", "start", "stop", "export", "destroy"} <= operations


def test_compose_json_accepts_array_and_json_lines():
    controller = load_controller()
    assert controller.compose_json('[{"Service":"db"}]') == [{"Service": "db"}]
    assert controller.compose_json('{"Service":"db"}\n{"Service":"odoo"}') == [
        {"Service": "db"}, {"Service": "odoo"}
    ]
