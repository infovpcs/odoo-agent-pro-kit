"""Phase 10: per-session Python requirements and imported custom modules (real 19→20 migration)."""
import hashlib
import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_controller():
    loader = importlib.machinery.SourceFileLoader("sandboxctl", str(ROOT / "sandbox/bin/sandboxctl"))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_requirements_accept_plain_pinned_and_commented_lines():
    controller = load_controller()
    text = "# LLM deps\nopenai>=1.0.0\nanthropic>=0.18.0,<1\ngoogle-generativeai>=0.3.0\nhttpx[http2]==0.27.0\nollama>=0.1.0  # local client\n\n"
    assert controller.parse_requirements(text) == [
        "openai>=1.0.0", "anthropic>=0.18.0,<1", "google-generativeai>=0.3.0", "httpx[http2]==0.27.0", "ollama>=0.1.0",
    ]


@pytest.mark.parametrize("line", [
    "-e git+https://github.com/x/y.git#egg=y",
    "--index-url https://evil.example/simple",
    "--extra-index-url https://evil.example/simple",
    "-r other.txt",
    "https://example.com/pkg.whl",
    "./local/path",
    "pkg @ https://example.com/pkg.whl",
    "pkg; os_name == 'nt'; rm -rf /",
])
def test_requirements_reject_options_urls_and_paths(line):
    controller = load_controller()
    with pytest.raises(SystemExit):
        controller.parse_requirements(line + "\n")


def test_requirements_image_tag_is_content_addressed():
    controller = load_controller()
    base = "odoo-agent-dev:20-008173c2abcd"
    lines = ["openai>=1.0.0", "httpx>=0.24.0"]
    digest = hashlib.sha256("\n".join(lines).encode() + b"\n").hexdigest()[:12]
    assert controller.requirements_image(base, lines) == f"{base}-req{digest}"
    assert controller.requirements_image(base, list(reversed(lines))) != controller.requirements_image(base, lines)


def test_requirements_dockerfile_overlays_a_venv_without_replacing_debian_packages():
    dockerfile = (ROOT / "sandbox/images/odoo-dev/requirements.Dockerfile").read_text()
    assert "ARG ODOO_DEV_IMAGE" in dockerfile and "FROM ${ODOO_DEV_IMAGE}" in dockerfile
    assert "python3 -m venv --without-pip --system-site-packages /opt/sandbox-venv" in dockerfile
    assert "/opt/sandbox-venv/bin/python3 -m pip install --no-cache-dir -r /tmp/sandbox-requirements.txt" in dockerfile
    # --ignore-installed replaced Debian's cryptography and broke pyOpenSSL (base failed to load).
    assert "--ignore-installed" not in dockerfile and "--break-system-packages" not in dockerfile
    assert "pip freeze --path /opt/sandbox-site-packages > /opt/sandbox-requirements.freeze" in dockerfile
    assert 'python3 -c "import odoo.addons.base.models"' in dockerfile
    assert "ENV PYTHONPATH=/opt/sandbox-site-packages" in dockerfile
    assert dockerfile.rstrip().splitlines()[-1] == "USER odoo"


def test_create_builds_requirements_layer_after_base_build_and_before_schema_init():
    controller = (ROOT / "sandbox/bin/sandboxctl").read_text()
    base_build = controller.index('compose(session, "build", "--pull", "odoo")')
    layer = controller.index("build_requirements_image(session", base_build)
    initialize = controller.index('"--init", "base"', base_build)
    assert base_build < layer < initialize


def test_create_cli_accepts_requirements_and_import():
    result = subprocess.run([str(ROOT / "sandbox/bin/sandboxctl"), "create", "--help"], capture_output=True, text=True, check=True)
    assert "--requirements" in result.stdout
    assert "--import" in result.stdout


def _module(root, name, depends=("base",)):
    (root / name).mkdir(parents=True)
    (root / name / "__manifest__.py").write_text(json.dumps({"name": name, "version": "19.0.1.0.0", "depends": list(depends)}))
    (root / name / "__init__.py").write_text("")


def test_import_copies_every_module_and_skips_non_modules(tmp_path):
    controller = load_controller()
    source = tmp_path / "20-apps"
    _module(source, "vpcs_llm_provider")
    _module(source, "vpcs_progressive_payment_terms")
    (source / "docs").mkdir()
    (source / "migration-report.json").write_text("{}")
    target = tmp_path / "addons"
    target.mkdir()
    copied = controller.prepare_import(source, target, "vpcs_llm_provider")
    assert copied == ["vpcs_llm_provider", "vpcs_progressive_payment_terms"]
    assert (target / "vpcs_progressive_payment_terms/__manifest__.py").is_file()
    assert not (target / "docs").exists()


def test_import_requires_the_primary_module(tmp_path):
    controller = load_controller()
    source = tmp_path / "20-apps"
    _module(source, "other_module")
    with pytest.raises(SystemExit):
        controller.prepare_import(source, tmp_path, "vpcs_llm_provider")


def test_import_accepts_a_single_module_directory(tmp_path):
    controller = load_controller()
    _module(tmp_path, "vpcs_llm_provider")
    target = tmp_path / "addons"
    target.mkdir()
    assert controller.prepare_import(tmp_path / "vpcs_llm_provider", target, "vpcs_llm_provider") == ["vpcs_llm_provider"]


def test_import_refuses_symlinks_that_escape_the_source(tmp_path):
    controller = load_controller()
    source = tmp_path / "apps"
    _module(source, "vpcs_llm_provider")
    (source / "vpcs_llm_provider" / "leak").symlink_to("/etc")
    target = tmp_path / "addons"
    target.mkdir()
    with pytest.raises(SystemExit):
        controller.prepare_import(source, target, "vpcs_llm_provider")


def test_kit_allows_pypi_for_session_requirements():
    spec = (ROOT / "sandbox/kits/odoo-mixin/spec.yaml").read_text()
    assert "- pypi.org" in spec
    assert "- files.pythonhosted.org" in spec
    lock = json.loads((ROOT / "sandbox/config/artifacts.lock").read_text())
    kit = lock["kits"]["odoo-mixin"]
    assert kit["version"] == "0.7.0" and "version: 0.7.0" in spec
    assert kit["spec_sha256"] == hashlib.sha256((ROOT / kit["path"] / "spec.yaml").read_bytes()).hexdigest()
