from __future__ import annotations
from plugin.hooks.checks import paths


def _kinds(vs):
    return sorted(v.kind for v in vs)


def test_enterprise_path_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "addons" / "web_studio" / "x.py"), "x = 1\n", tmp_path)
    assert "enterprise_source" in _kinds(vs)


def test_enterprise_license_content_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "mymod" / "__manifest__.py"),
                          '{"name": "x", "license": "OEEL-1"}\n', tmp_path)
    assert "enterprise_source" in _kinds(vs)


def test_private_key_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    body = "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----\n"
    vs = paths.scan_write(str(tmp_path / "notes.txt"), body, tmp_path)
    assert "secret_material" in _kinds(vs)


def test_env_example_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / ".env.example"), "API_TOKEN=abc123def456\n", tmp_path)
    assert vs == []


def test_outside_repo_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    outside = tmp_path.parent / "elsewhere" / "secret.txt"
    vs = paths.scan_write(str(outside), "ghp_" + "a" * 36, tmp_path)
    assert vs == []


def test_clean_write_ok(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "mymod" / "models" / "m.py"), "class X: pass\n", tmp_path)
    assert vs == []


def test_env_line_in_real_env_file_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / ".env"), "API_TOKEN=abc123def456ghi\n", tmp_path)
    assert "secret_material" in _kinds(vs)


def test_env_line_in_python_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    body = "SECRET_KEY = fields.Char()\nAUTH_TOKEN = os.environ.get(\"AUTH_TOKEN\")\n"
    vs = paths.scan_write(str(tmp_path / "mymod" / "models" / "m.py"), body, tmp_path)
    assert vs == []


def test_enterprise_license_in_doc_not_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "docs" / "migration_notes.md"),
                          "The module was OEEL-1 licensed.\n", tmp_path)
    assert vs == []


def test_enterprise_license_in_manifest_flagged(tmp_path):
    (tmp_path / ".git").mkdir()
    vs = paths.scan_write(str(tmp_path / "mymod" / "__manifest__.py"),
                          '{"name": "x", "license": "OEEL-1"}\n', tmp_path)
    assert "enterprise_source" in _kinds(vs)
