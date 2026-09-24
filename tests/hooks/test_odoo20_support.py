"""Odoo 20.0 support, with 17.0/18.0/19.0 behaviour kept unchanged.

Evidence for each Odoo 20 rule was read from odoo/odoo@20.0
d3236ca5c7052e892a097b007c38b9501888e406 (see docs/odoo-20-migration-roadmap.md).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from plugin.hooks.checks import common, odoo_lint, version

REPO = Path(__file__).resolve().parents[2]


def _rules(findings):
    return sorted(f.rule for f in findings)


def _sev(findings, rule):
    return next(f.severity for f in findings if f.rule == rule)


# --- version detection -------------------------------------------------------

def test_detect_20_from_sandbox_session(tmp_path, monkeypatch):
    (tmp_path / ".sandbox").mkdir()
    (tmp_path / ".sandbox" / "session.json").write_text(json.dumps({"odoo_version": "20.0"}))
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(tmp_path) == "20"


def test_detect_20_from_version_dir(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "20.0").mkdir()
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "20"


def test_detect_20_from_module_meta_and_env(tmp_path, monkeypatch):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [ ] t\n")
    (mod / "docs" / "module_meta.md").write_text("odoo_version: 20.0\n")
    monkeypatch.delenv("DEFAULT_ODOO_VERSION", raising=False)
    assert version.detect_odoo_version(mod) == "20"
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", "20.0")
    assert version.detect_odoo_version(tmp_path) == "20"


@pytest.mark.parametrize("v", ["17", "18", "19"])
def test_previous_versions_still_detected(tmp_path, monkeypatch, v):
    monkeypatch.setenv("DEFAULT_ODOO_VERSION", f"{v}.0")
    assert version.detect_odoo_version(tmp_path) == v


def test_unsupported_versions_rejected(tmp_path, monkeypatch):
    for bad in ("16.0", "21.0", "2.0"):
        monkeypatch.setenv("DEFAULT_ODOO_VERSION", bad)
        assert version.detect_odoo_version(tmp_path) is None


def test_find_module_dir_by_20_dir_and_version_token(tmp_path):
    ws = tmp_path / "ws"
    (ws / "20.0").mkdir(parents=True)
    assert common.find_module_dir(ws) == ws.resolve()
    mod = tmp_path / "mymod"
    mod.mkdir()
    assert common.resolve_module_dir(tmp_path, "/testing 20 mymod") == mod.resolve()
    assert common.resolve_module_dir(tmp_path, "20.0 mymod") == mod.resolve()


# --- lint: existing rules carry forward to 20 --------------------------------

@pytest.mark.parametrize("rule,path,content", [
    ("L1", "m/views/x.xml", "<tree/>"),
    ("L2", "m/views/v.xml", '<field name="x" attrs="{}"/>'),
    ("L3", "m/controllers/main.py", "@http.route('/x', type='json')\n"),
    ("L4", "m/views/s.xml", '<search><group expand="0"/></search>'),
    ("L5", "m/security/g.xml",
     '<record model="res.groups"><field name="category_id" ref="x"/></record>'),
])
def test_19_block_rules_also_block_on_20(rule, path, content):
    f = odoo_lint.lint(path, content, "20")
    assert rule in _rules(f) and _sev(f, rule) == "block"


# --- lint: new Odoo 20 rules --------------------------------------------------

def test_l7_ir_model_access_csv_blocks_on_20_only():
    csv = "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
    f20 = odoo_lint.lint("m/security/ir.model.access.csv", csv, "20")
    assert "L7" in _rules(f20) and _sev(f20, "L7") == "block"
    assert "ir.access.csv" in next(x.fix for x in f20 if x.rule == "L7")
    for v in ("17", "18", "19"):
        assert "L7" not in _rules(odoo_lint.lint("m/security/ir.model.access.csv", csv, v))


def test_l7_new_ir_access_csv_is_clean_on_20():
    csv = "id,name,model_id,group_id/id,operation,domain\naccess_x,x,model_x,base.group_user,crud,\n"
    assert odoo_lint.lint("m/security/ir.access.csv", csv, "20") == []


def test_l8_ir_rule_record_blocks_on_20_only():
    xml = '<odoo><record id="r" model="ir.rule"><field name="domain_force">[]</field></record></odoo>'
    f20 = odoo_lint.lint("m/security/rules.xml", xml, "20")
    assert "L8" in _rules(f20) and _sev(f20, "L8") == "block"
    for v in ("17", "18", "19"):
        assert "L8" not in _rules(odoo_lint.lint("m/security/rules.xml", xml, v))


def test_l9_tracking_value_model_warns_on_20_only():
    py = "vals = self.env['mail.tracking.value'].search([])\n"
    f20 = odoo_lint.lint("m/models/m.py", py, "20")
    assert "L9" in _rules(f20) and _sev(f20, "L9") == "warn"
    assert "mail_tracking" in next(x.fix for x in f20 if x.rule == "L9")
    assert "L9" not in _rules(odoo_lint.lint("m/models/m.py", py, "19"))


def test_l10_font_awesome_in_view_warns_on_20_only():
    xml = '<odoo><template id="t"><i class="fa fa-check"/></template></odoo>'
    f20 = odoo_lint.lint("m/views/t.xml", xml, "20")
    assert "L10" in _rules(f20) and _sev(f20, "L10") == "warn"
    assert "L10" not in _rules(odoo_lint.lint("m/views/t.xml", xml, "19"))


def test_17_behaviour_unchanged():
    assert "L1" not in _rules(odoo_lint.lint("m/views/x.xml", "<tree/>", "17"))


# --- surfaces that must advertise 20 ------------------------------------------

def test_sandbox_schema_matches_pinned_images():
    """Sandbox only advertises versions with a pinned base image.

    No official odoo:20.0 image exists on Docker Hub as of 2026-09-24, so 20.0 is
    added to the sandbox only together with a verified images.lock digest.
    """
    schema = json.loads((REPO / "sandbox/schemas/session.schema.json").read_text())
    versions = json.loads((REPO / "sandbox/config/versions.yaml").read_text())
    locks = (REPO / "sandbox/config/images.lock").read_text()
    enum = schema["properties"]["odoo_version"]["enum"]
    assert enum == sorted(v["series"] for v in versions.values())
    for v in versions.values():
        assert f"{v['base_image_lock']}=" in locks


def test_odoo20_skills_exist_with_frontmatter():
    for name, slug in (("Odoo20CodingStandard", "odoo_20_coding_standard"),
                       ("OdooTools20", "odoo_tools_20"),
                       ("Odoo20ExistingDependencyContext", "odoo_20_dependency_context")):
        text = (REPO / "plugin/skills" / name / "SKILL.md").read_text()
        assert text.startswith("---\n")
        assert f"name: {slug}\n" in text
        assert 'odoo_versions: ["20.0"]' in text


def test_plugin_manifest_tags_and_prompts_include_20():
    manifest = (REPO / "plugin/plugin.yaml").read_text()
    assert '"odoo-20"' in manifest
    init = (REPO / "plugin/__init__.py").read_text()
    assert "<17|18|19|20>" in init
    assert "(17, 18, 19, or 20)" in init


# --- MCP discovery + Hermes command parsing -----------------------------------

def test_mcp_protocol_for_20_is_json_rpc_like_19():
    pytest.importorskip("pydantic")
    from plugin.odoo_mcp.config import load_config
    from plugin.odoo_mcp.version_detector import VersionDetector
    cfg = load_config("20.0")
    assert cfg.protocol == "json-rpc-2.0"
    det = VersionDetector(cfg)
    assert det.get_protocol("20.0") == "json-rpc-2.0"
    assert det.get_protocol("19.0") == "json-rpc-2.0"
    assert det.get_protocol("18.0") == "xml-rpc"
    assert det.get_protocol("17.0") == "xml-rpc"


def test_mcp_default_port_for_20():
    pytest.importorskip("pydantic")
    from plugin.odoo_mcp.config import load_config
    assert load_config("20.0").mcp_server_port == 8768
    assert load_config("19.0").mcp_server_port == 8767


def test_hermes_command_parser_accepts_20():
    import plugin as kit
    assert kit._parse_version_and_rest("20 my_mod") == ("20", "my_mod")
    assert kit._parse_version_and_rest("19 my_mod") == ("19", "my_mod")
    assert kit._parse_version_and_rest("21 my_mod") == (None, "21 my_mod")


def test_deepseek_preset_knows_20():
    mjs = (REPO / "integrations/deepseek/preset/odoo-kit.mjs").read_text()
    assert "const VERSIONS = ['20.0', '19.0', '18.0', '17.0']" in mjs
    assert "'20': '20.0'" in mjs and "'20.0': '20.0'" in mjs


def test_l5_does_not_span_into_a_following_privilege_record():
    """Regression: odoo/odoo@20.0 addons/account/security/account_security.xml was flagged.

    A res.groups record followed by a res.groups.privilege record (whose category_id is
    correct) must not be reported; the match may not cross </record>.
    """
    xml = (
        '<record id="group_a" model="res.groups"><field name="name">A</field></record>\n'
        '<record id="priv_b" model="res.groups.privilege"><field name="name">B</field>'
        '<field name="category_id" ref="base.module_category_x"/></record>'
    )
    for v in ("19", "20"):
        assert "L5" not in _rules(odoo_lint.lint("m/security/s.xml", xml, v))
