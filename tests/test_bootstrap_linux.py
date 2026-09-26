"""Linux bootstrap (bootstrap_odoo_env.sh) must work on current Ubuntu.

Ubuntu 23.04+ marks the system Python "externally managed" (PEP 668), so
`pip install uv` into python3.12 is refused. Found by an end-to-end run in a
fresh ubuntu:24.04 container on 2026-09-26.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "odoo_local_setup" / "bootstrap_odoo_env.sh"


def test_uv_does_not_depend_on_pip_into_system_python():
    body = SCRIPT.read_text()
    assert "python3.12 -m uv" not in body
    assert "python3.12 -m pip install --upgrade uv" not in body
    assert "https://astral.sh/uv/install.sh" in body


def test_bash_syntax():
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_postgres_is_started_when_not_running():
    body = SCRIPT.read_text()
    assert "pg_isready" in body and "service postgresql start" in body


def test_workspace_env_records_kit_home_for_mcp():
    body = SCRIPT.read_text()
    assert "ODOO_AGENT_PRO_KIT_HOME=" in body


def test_resolve_uv_prefers_existing_binary(tmp_path):
    body = SCRIPT.read_text()
    fn = body[body.index("resolve_uv() {"):body.index("\n}\n", body.index("resolve_uv() {")) + 3]
    fake = tmp_path / "uv"
    fake.write_text("#!/bin/sh\necho fake-uv\n")
    fake.chmod(0o755)
    out = subprocess.run(["bash", "-c", "die(){ echo DIE; exit 1; }\n" + fn + "\nresolve_uv; echo \"$UV_BIN\""],
                         capture_output=True, text=True, env={"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)})
    assert out.stdout.strip().endswith(str(fake))


def test_deb_only_python_deps_installed_for_17_plus_on_linux_and_macos():
    # Odoo ships python3-phonenumbers / python3-renderpm via debian/control; requirements.txt
    # omits them off Windows. Without them phone_validation, account supplier-invoice import
    # and reportlab QR/barcode rendering (_rl_renderPM) tests fail on 20.
    linux = SCRIPT.read_text()
    assert 'pip install --python "$odoo_dir/.venv/bin/python" phonenumbers rl-renderPM' in linux
    macos = (REPO / "odoo_local_setup" / "setup_local_macos.sh").read_text()
    assert 'UV_DEPS="$UV_DEPS num2words xlwt pypdf phonenumbers rl-renderPM"' in macos


def test_libmagic_installed_for_python_magic():
    # Without libmagic1, python-magic fails to import and Odoo 20's fallback
    # mimetype guesser raises on BinaryBytes (base test_avatar_mixin).
    assert " libmagic1 " in SCRIPT.read_text()


def test_linux_bootstrap_installs_pinned_patched_wkhtmltopdf():
    # Odoo's PDF reports need wkhtmltopdf 0.12.6 with patched Qt; the Linux bootstrap
    # installed none, so report printing could not work on Linux workspaces.
    body = SCRIPT.read_text()
    assert "wkhtmltox_0.12.6.1-3" in body and "sha256sum" in body
    for sha in ("4f723b2691ad8638a9df960e0421d346d7315083e3583a334f33362280ddba15",   # jammy amd64
                "2095f20256661ebf0983b9311168596c9d012666e21a94bc24f304db6ac69ec5",   # jammy arm64
                "98ba0d157b50d36f23bd0dedf4c0aa28c7b0c50fcdcdc54aa5b6bbba81a3941d",   # bookworm amd64
                "b6606157b27c13e044d0abbe670301f88de4e1782afca4f9c06a5817f3e03a9c"):  # bookworm arm64
        assert sha in body
    assert "patched qt" in body


def _wk_select(codename, arch):
    body = SCRIPT.read_text()
    fn = body[body.index("wkhtmltopdf_deb_for() {"):body.index("\n}\n", body.index("wkhtmltopdf_deb_for() {")) + 3]
    out = subprocess.run(["bash", "-c", fn + f"\nwkhtmltopdf_deb_for {codename} {arch}"],
                         capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    return out.stdout.strip()


def test_wkhtmltopdf_deb_selection():
    assert _wk_select("noble", "amd64").startswith("jammy_amd64 4f723b26")
    assert _wk_select("jammy", "arm64").startswith("jammy_arm64 2095f202")
    assert _wk_select("bookworm", "amd64").startswith("bookworm_amd64 98ba0d15")
    assert _wk_select("focal", "amd64") == ""


def test_macos_setup_checks_wkhtmltopdf():
    body = (REPO / "odoo_local_setup" / "setup_local_macos.sh").read_text()
    assert "wkhtmltopdf" in body and "patched qt" in body and "macos-cocoa.pkg" in body


def test_bootstrap_sh_keeps_a_single_kit_home_line(tmp_path):
    body = (REPO / "bootstrap.sh").read_text()
    start = body.index("  # bootstrap_odoo_env.sh may already have written")
    block = body[start:body.index("\n  fi\n", start) + 6]
    env = tmp_path / ".env"
    env.write_text("ODOO_AGENT_PRO_KIT_HOME=/old\nOTHER=1\n")
    subprocess.run(["bash", "-c", f'ws="{tmp_path}"; REPO_ROOT=/kit\n{block}'], check=True)
    lines = env.read_text().splitlines()
    assert lines.count('export ODOO_AGENT_PRO_KIT_HOME="/kit"') == 1
    assert not any(l.startswith("ODOO_AGENT_PRO_KIT_HOME=") for l in lines) and "OTHER=1" in lines
