"""Phase 10: Odoo 20.0 in the Docker Sandbox.

Docker Hub published the official `odoo:20.0` image (index digest checked 2026-10-09, release
20260926), so the Odoo 20 dev image is the same thin dev layer as 17/18/19 on that pinned
digest. Until then the kit reproduced the `odoo/docker` 20.0 recipe on `ubuntu:noble`.
Odoo 20 needs PostgreSQL >= 16 (`odoo/release.py` MIN_PG_VERSION) and replaced
`ir.model.access` with `ir.access`. 17/18/19 must stay exactly as they were.
"""
import importlib.machinery
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UNCHANGED_LOCKS = {
    "ODOO_17_BASE": "odoo:17.0@sha256:4959237918da385a5befe007fc95177bc2244c048ebc55097b7aa71c703e70ba",
    "ODOO_18_BASE": "odoo:18.0@sha256:4ea9b4667921130add13c1b859aa170a4572b5c3c3d747bfb0ef152fdb0b48a7",
    "ODOO_19_BASE": "odoo:19.0@sha256:94a4f480b8039dc9ca2bca9e77e59f97d3311f66e2aad663cf2670be9c66d4ea",
    "POSTGRES_15": "postgres:15-bookworm@sha256:e8db9bd3e9e1751eb639fb17be53cc6d1b62a322adf75b99e791767a7a16ce69",
}


def load_controller(name="sandboxctl_phase10"):
    path = ROOT / "sandbox/bin/sandboxctl"
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def locks():
    text = (ROOT / "sandbox/config/images.lock").read_text()
    return dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#"))


def versions():
    return json.loads((ROOT / "sandbox/config/versions.yaml").read_text())


def test_odoo20_and_postgres16_are_digest_pinned_and_older_locks_are_unchanged():
    values = locks()
    for key, value in UNCHANGED_LOCKS.items():
        assert values[key] == value
    assert re.fullmatch(r"odoo:20\.0@sha256:[0-9a-f]{64}", values["ODOO_20_BASE"])
    assert re.fullmatch(r"postgres:16-bookworm@sha256:[0-9a-f]{64}", values["POSTGRES_16"])


def test_versions_yaml_adds_20_on_postgres16_json2_and_keeps_17_to_19():
    data = versions()
    assert set(data) == {"17", "18", "19", "20"}
    for major in ("17", "18", "19"):
        assert data[major]["postgres_image_lock"] == "POSTGRES_15"
        assert data[major]["base_image_lock"] == f"ODOO_{major}_BASE"
    assert data["20"] == {
        "series": "20.0",
        "base_image_lock": "ODOO_20_BASE",
        "dockerfile": "sandbox/images/odoo-dev/20.Dockerfile",
        "postgres_image_lock": "POSTGRES_16",
        "rpc_protocol": "json2",
        "addons_path": "/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons",
    }


def test_odoo20_dockerfile_is_the_dev_layer_on_the_official_image():
    """Same file as 17/18/19: the official image already carries Odoo, wkhtmltopdf and the
    PostgreSQL client, so nothing is downloaded or installed at build time."""
    text = (ROOT / "sandbox/images/odoo-dev/20.Dockerfile").read_text()
    reference = (ROOT / "sandbox/images/odoo-dev/19.Dockerfile").read_text()
    assert text == reference.replace("odoo:19.0", "odoo:20.0")
    assert "ARG ODOO_BASE_IMAGE=odoo:20.0\nFROM ${ODOO_BASE_IMAGE}\n" in text
    for leftover in ("ubuntu:noble", "apt-get", "curl", "nightly.odoo.com", "keyserver", "sha1sum", "ADD "):
        assert leftover not in text
    assert "0\\.12\\.6.*patched qt" in text
    assert text.index("USER odoo") > text.index("odoo-healthcheck")


def test_session_schema_and_controller_accept_20():
    schema = json.loads((ROOT / "sandbox/schemas/session.schema.json").read_text())
    assert schema["properties"]["odoo_version"]["enum"] == ["17.0", "18.0", "19.0", "20.0"]
    controller = load_controller()
    for requested in ("20", "20.0"):
        major, config = controller.version_config(requested)
        assert major == "20" and config["postgres_image_lock"] == "POSTGRES_16"
    with pytest.raises(SystemExit, match="17, 18, 19, or 20"):
        controller.version_config("16")


def test_fleet_accepts_20():
    text = (ROOT / "sandbox/bin/sandbox-fleet").read_text()
    assert '{"17", "18", "19", "20"}' in text
    command = (ROOT / "plugin/commands/fleet.md").read_text()
    assert "<17|18|19|20>" in command
    assert "Odoo 20 is not accepted here yet" not in command


def test_matrix_scripts_and_release_workflow_include_20():
    assert '"${SANDBOX_LIFECYCLE_VERSIONS:-17 18 19 20}"' in (ROOT / "sandbox/tests/lifecycle.sh").read_text()
    assert "for version in 17 18 19 20; do" in (ROOT / "sandbox/tests/multiarch-build.sh").read_text()
    assert "17|18|19|20" in (ROOT / "sandbox/tests/ci-smoke.sh").read_text()
    workflow = (ROOT / ".github/workflows/docker-sandbox-release.yml").read_text()
    assert workflow.count("version: [17, 18, 19, 20]") == 2
    assert '"17", "18", "19", "20"' in (ROOT / "sandbox/scripts/migrate-local.py").read_text()


def fixture_files(tmp_path, series):
    controller = load_controller(f"sandboxctl_fixture_{series[:2]}")
    target = tmp_path / "sandbox_fixture"
    controller.prepare_fixture(ROOT / "sandbox/fixtures/sandbox_fixture", target, series)
    manifest = (target / "__manifest__.py").read_text()
    return target, manifest


def test_fixture_for_20_uses_ir_access_and_older_versions_are_unchanged(tmp_path):
    target, manifest = fixture_files(tmp_path / "20", "20.0")
    assert '"version": "20.0.1.0.0"' in manifest
    assert "security/ir.access.csv" in manifest
    assert "ir.model.access.csv" not in manifest
    assert not (target / "security/ir.model.access.csv").exists()
    rows = (target / "security/ir.access.csv").read_text().splitlines()
    assert rows[0] == "id,name,model_id,group_id/id,operation,domain"
    assert rows[1] == "access_sandbox_fixture,sandbox.fixture,sandbox.fixture,base.group_user,crud,"
    for series in ("17.0", "18.0", "19.0"):
        target, manifest = fixture_files(tmp_path / series, series)
        assert f'"version": "{series}.1.0.0"' in manifest
        assert "security/ir.model.access.csv" in manifest
        assert not (target / "security/ir.access.csv").exists()


def test_json2_lifecycle_reports_the_session_series_not_a_hardcoded_19():
    text = (ROOT / "sandbox/scripts/fixture-lifecycle.py").read_text()
    assert 'return "19.0"' not in text
    assert 'os.environ["ODOO_VERSION"]' in text


def test_mcp_sidecar_uses_the_session_api_key_and_the_20_port():
    override = (ROOT / "sandbox/mcp-sidecar/mcp.override.yaml").read_text()
    assert "ODOO_API_KEY: ${ODOO_API_KEY:-}" in override
    up = (ROOT / "sandbox/mcp-sidecar/mcp_up.sh").read_text()
    assert "19.0) MCP_PORT=8767 ;;" in up
    assert "20.0) MCP_PORT=8768 ;;" in up


def test_json2_versions_get_an_rpc_api_key_at_create():
    """20 shares 19's json2 path, which writes ODOO_API_KEY into runtime.env."""
    text = (ROOT / "sandbox/bin/sandboxctl").read_text()
    assert "_generate('rpc'" in text
    assert versions()["20"]["rpc_protocol"] == "json2"


def test_kit_allows_the_odoo20_build_egress_and_digest_matches_the_lock():
    import hashlib
    spec = (ROOT / "sandbox/kits/odoo-mixin/spec.yaml").read_text()
    for host in ("archive.ubuntu.com", "security.ubuntu.com", "ports.ubuntu.com", "apt.postgresql.org",
                 "keyserver.ubuntu.com", "nightly.odoo.com", "registry.npmjs.org",
                 "release-assets.githubusercontent.com", "objects.githubusercontent.com"):
        assert f"      - {host}\n" in spec
    assert "Odoo 17, 18, 19, and 20" in spec
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    kit = lock["kits"]["odoo-mixin"]
    assert kit["spec_sha256"] == hashlib.sha256(spec.encode()).hexdigest()
    assert f"version: {kit['version']}\n" in spec and lock["release"] == kit["version"]


def test_shell_scripts_set_config_parameters_on_every_series():
    """Odoo 20 removed ir.config_parameter.set_param (AttributeError; found by ci-smoke 20)."""
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    smoke = (ROOT / "sandbox/scripts/report-pdf-smoke.py").read_text()
    for text in (controller, smoke):
        assert "set_str if hasattr(" in text
        assert re.search(r"\]\.sudo\(\)\.set_param\(", text) is None


def test_odoo_listens_on_the_compose_network():
    """Odoo 20 defaults http_interface to 127.0.0.1 (odoo/tools/config.py); 17-19 bound all
    interfaces. Sidecars and run-mode probes reach Odoo at http://odoo:8069."""
    template = (ROOT / "sandbox/config/odoo.conf.template").read_text()
    assert "\nhttp_interface = 0.0.0.0\n" in template


def test_lifecycle_health_poll_is_quiet():
    """While Odoo restarts, each refused /web/health probe printed a full urllib traceback
    (the run still passed). The readiness poll must discard its expected errors."""
    text = (ROOT / "sandbox/tests/lifecycle.sh").read_text()
    poll = next(line for line in text.splitlines() if '"/web/health", timeout=2' in line)
    assert poll.rstrip().endswith("2>/dev/null; then")
