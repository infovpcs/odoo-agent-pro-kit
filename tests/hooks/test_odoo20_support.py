"""Odoo 20.0 support, with 17.0/18.0/19.0 behaviour kept unchanged.

Evidence for each Odoo 20 rule was read from odoo/odoo@20.0
d3236ca5c7052e892a097b007c38b9501888e406 (see docs/odoo-20-migration-roadmap.md).
"""
from __future__ import annotations

import json
import subprocess
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


def test_l11_toggle_active_and_boolean_button_block_on_20_only():
    """Found by a live 19->20 migration: odoo/odoo@20.0 has no BaseModel.toggle_active
    (19.0 had it at odoo/orm/models.py) and no boolean_button widget; upgrade_code does
    not rewrite either, so install fails with "toggle_active is not a valid action"."""
    xml = ('<form><sheet><div name="button_box"><button name="toggle_active" type="object">'
           '<field name="active" widget="boolean_button"/></button></div></sheet></form>')
    f20 = odoo_lint.lint("m/views/v.xml", xml, "20")
    assert "L11" in _rules(f20) and _sev(f20, "L11") == "block"
    assert "action_archive" in next(x.fix for x in f20 if x.rule == "L11")
    assert "L11" in _rules(odoo_lint.lint("m/models/m.py", "rec.toggle_active()\n", "20"))
    for v in ("17", "18", "19"):
        assert "L11" not in _rules(odoo_lint.lint("m/views/v.xml", xml, v))
    assert "L11" not in _rules(odoo_lint.lint("m/views/v.xml", '<field name="active" widget="boolean_toggle"/>', "20"))


def test_l12_t_esc_in_view_arch_blocks_on_20_only():
    """Found by a live 19->20 migration: Odoo 20 rejects t-esc in kanban/card view arch
    ("Forbidden owl directive used in arch (t-esc)", ir_ui_view.py allowed_directives),
    and upgrade_code's owl3 t-esc rewrite only touches /static/ files, not views/*.xml."""
    xml = '<card><footer><t t-esc="record.x.value"/></footer></card>'
    f20 = odoo_lint.lint("m/views/v.xml", xml, "20")
    assert "L12" in _rules(f20) and _sev(f20, "L12") == "block"
    assert "t-out" in next(x.fix for x in f20 if x.rule == "L12")
    for v in ("17", "18", "19"):
        assert "L12" not in _rules(odoo_lint.lint("m/views/v.xml", xml, v))
    assert "L12" not in _rules(odoo_lint.lint("m/views/v.xml", '<t t-out="record.x.value"/>', "20"))


def test_l13_registry_init_flag_blocks_on_20_only():
    """Found by a live 19->20 migration: odoo/orm/registry.py on 20.0 no longer sets
    Registry._init (19.0 did), so `self.env.registry._init` raises AttributeError in
    constraints/computes at runtime; lint cannot see it at install time."""
    py = "if self.env.registry._init:\n    return\n"
    f20 = odoo_lint.lint("m/models/m.py", py, "20")
    assert "L13" in _rules(f20) and _sev(f20, "L13") == "block"
    assert "registry.ready" in next(x.fix for x in f20 if x.rule == "L13")
    for v in ("17", "18", "19"):
        assert "L13" not in _rules(odoo_lint.lint("m/models/m.py", py, v))
    assert "L13" not in _rules(odoo_lint.lint("m/models/m.py", "self._init_column('x')\n", "20"))


# --- Lifecycle commands / skill routing ----------------------------------------

_LIFECYCLE = ("plan-analysis", "start-coding", "testing")


def test_lifecycle_commands_accept_20_but_fleet_stays_sandbox_bound():
    for name in _LIFECYCLE:
        text = (REPO / "plugin" / "commands" / f"{name}.md").read_text()
        assert "<17|18|19|20>" in text and "17, 18, 19, or 20" in text, name
        assert "17, 18, or 19" not in text, name
        cur = (REPO / "integrations" / "cursor" / "commands" / f"{name}.md").read_text()
        assert "17|18|19|20" in cur, name
        vs = (REPO / "integrations" / "vscode" / "prompts" / f"{name}.prompt.md").read_text()
        assert "17, 18, 19, or 20" in vs, name
    fleet = (REPO / "plugin" / "commands" / "fleet.md").read_text()
    assert "<17|18|19>" in fleet and "Docker Sandbox" in fleet


def test_commanding_system_routes_20_to_the_20_skills():
    text = (REPO / "plugin" / "skills" / "CommandingSystem" / "SKILL.md").read_text()
    block = text[text.index("### Odoo 20"):text.index("### Odoo 19")]
    for skill in ("Odoo20CodingStandard", "OdooTools20", "Odoo20ExistingDependencyContext"):
        assert skill in block
    wf = (REPO / "plugin" / "skills" / "CommandingSystem" / "start_coding_workflow.md").read_text()
    assert "**Odoo 20 standards:**" in wf and "ir.access.csv" in wf


def _mcp_launcher_port(version):
    script = REPO / "plugin" / "odoo_mcp" / "start_mcp_server.sh"
    body = script.read_text()
    fn = body[body.index("get_major_version() {"):body.index("get_pid_file_for_version()")] \
        if "get_pid_file_for_version()" in body else None
    assert fn, "launcher helpers moved"
    out = subprocess.run(["bash", "-c", fn + f"\nget_mcp_port_for_version {version}"],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def test_mcp_launcher_ports_and_20_credentials():
    assert [_mcp_launcher_port(v) for v in ("17.0", "18.0", "19.0", "20.0")] == \
        ["8765", "8766", "8767", "8768"]
    body = (REPO / "plugin" / "odoo_mcp" / "start_mcp_server.sh").read_text()
    assert '"20.0"' in body
    fn = body[body.index("resolve_odoo_target() {"):body.index("# Print colored message")]
    out = subprocess.run(["bash", "-c", fn + '\nresolve_odoo_target 20; echo "$ODOO_T_URL|$ODOO_T_DB|$ODOO_T_API_KEY"'],
                         capture_output=True, text=True, check=True,
                         env={"PATH": "/usr/bin:/bin", "ODOO20_DB_NAME": "db20", "ODOO20_API_KEY": "k20",
                              "ODOO17_URL": "http://wrong:8017"})
    assert out.stdout.strip() == "http://localhost:8110|db20|k20"


# --- lint: 19.1-20.0 ORM changelog rules (evidence: odoo/odoo@20.0 87a1773b, ---------
# --- doc-20 content/developer/reference/backend/orm/changelog.rst) -------------------

def test_l14_config_parameter_get_set_param_blocks_on_20_only():
    py = ("ICP = self.env['ir.config_parameter'].sudo()\n"
          "url = ICP.get_param('web.base.url')\n")
    f20 = odoo_lint.lint("m/models/m.py", py, "20")
    assert "L14" in _rules(f20) and _sev(f20, "L14") == "block"
    assert _line_of_rule(f20, "L14") == 2
    assert "get_str" in next(x.fix for x in f20 if x.rule == "L14")
    setter = "self.env['ir.config_parameter'].set_param('k', True)\n"
    assert "L14" in _rules(odoo_lint.lint("m/controllers/c.py", setter, "20"))
    for v in ("17", "18", "19"):
        assert "L14" not in _rules(odoo_lint.lint("m/models/m.py", py, v))


def test_l14_ignores_email_message_get_param():
    # addons/mail/models/mail_thread.py on 20.0 legitimately calls email.message.get_param
    py = "if not part.get_param('charset'):\n    pass\n"
    assert "L14" not in _rules(odoo_lint.lint("m/models/m.py", py, "20"))
    typed = "self.env['ir.config_parameter'].sudo().get_str('web.base.url')\n"
    assert "L14" not in _rules(odoo_lint.lint("m/models/m.py", typed, "20"))
    # same file also using ir.config_parameter correctly must not flag the email call
    mixed = typed + "if not part.get_param('charset'):\n    pass\n"
    assert "L14" not in _rules(odoo_lint.lint("m/models/m.py", mixed, "20"))


def test_l14_detects_direct_chain_and_assigned_receiver():
    chain = "v = self.env['ir.config_parameter'].sudo().get_param('k', 'False')\n"
    assert "L14" in _rules(odoo_lint.lint("m/models/m.py", chain, "20"))
    chain2 = 'self.env["ir.config_parameter"].set_param("k", "v")\n'
    assert "L14" in _rules(odoo_lint.lint("m/models/m.py", chain2, "20"))
    assigned = ("IrConfigParam = self.env['ir.config_parameter'].sudo()\n"
                "if not part.get_param('charset'):\n    pass\n"
                "x = IrConfigParam.get_param('k')\n")
    f = odoo_lint.lint("m/models/m.py", assigned, "20")
    assert "L14" in _rules(f) and _line_of_rule(f, "L14") == 4


def test_l2_ignores_python_assignment_embedded_in_xml_data():
    # ent-20 hr_payroll/data/hr_payroll_warning_data.xml embeds `states = dict(...)` Python code
    xml = '<field name="code">\nstates = dict(run._fields["state"].get_description(env))\n</field>'
    for v in ("18", "19", "20"):
        assert "L2" not in _rules(odoo_lint.lint("m/data/d.xml", xml, v))
    assert "L2" in _rules(odoo_lint.lint("m/views/v.xml", "<field name='x' states='draft'/>", "19"))


def test_l15_table_query_blocks_on_20_only_including_report_dir():
    py = ("class R(models.Model):\n    _auto = False\n\n"
          "    @property\n    def _table_query(self):\n        return 'SELECT 1'\n")
    f20 = odoo_lint.lint("m/report/r.py", py, "20")
    assert "L15" in _rules(f20) and _sev(f20, "L15") == "block"
    assert "_table_sql" in next(x.fix for x in f20 if x.rule == "L15")
    for v in ("17", "18", "19"):
        assert "L15" not in _rules(odoo_lint.lint("m/report/r.py", py, v))
    ok = "    @property\n    def _table_sql(self):\n        return SQL('(SELECT 1)')\n"
    assert "L15" not in _rules(odoo_lint.lint("m/report/r.py", ok, "20"))


def test_l16_attachment_datas_field_blocks_on_20_only():
    # ir.attachment.datas was removed in 20.0: a write is silently dropped (file_size 0)
    py = "self.env['ir.attachment'].create({'name': 'a.pdf', 'datas': base64.b64encode(pdf).decode()})\n"
    f20 = odoo_lint.lint("m/wizard/w.py", py, "20")
    assert "L16" in _rules(f20) and _sev(f20, "L16") == "block"
    assert "'raw'" in next(x.fix for x in f20 if x.rule == "L16")
    assert "L16" in _rules(odoo_lint.lint("m/models/m.py", "data = att.datas\n", "20"))
    assert "L16" in _rules(odoo_lint.lint("m/controllers/c.py", "att.datas = payload\n", "20"))
    xml = '<record model="ir.attachment"><field name="datas" type="base64" file="m/static/a.pdf"/></record>'
    assert "L16" in _rules(odoo_lint.lint("m/data/d.xml", xml, "20"))
    for v in ("17", "18", "19"):
        assert "L16" not in _rules(odoo_lint.lint("m/wizard/w.py", py, v))
        assert "L16" not in _rules(odoo_lint.lint("m/data/d.xml", xml, v))
    assert "L16" not in _rules(odoo_lint.lint("m/models/m.py", "vals = {'raw': pdf}\n", "20"))
    # web/controllers/export.py on 20.0 reads an export_data() dict key named 'datas'
    assert "L16" not in _rules(odoo_lint.lint("m/controllers/c.py", "rows = res.get('datas', [])\n", "20"))


def test_l17_base64_bytes_written_to_a_field_warns_on_20_only():
    py = "partner.image_1920 = base64.b64encode(img)\n"
    f20 = odoo_lint.lint("m/models/m.py", py, "20")
    assert "L17" in _rules(f20) and _sev(f20, "L17") == "warn"
    assert "TypeError" in next(x.message for x in f20 if x.rule == "L17")
    assert "L17" in _rules(odoo_lint.lint("m/models/m.py", "vals = {'image_1920': base64.b64encode(img)}\n", "20"))
    for v in ("17", "18", "19"):
        assert "L17" not in _rules(odoo_lint.lint("m/models/m.py", py, v))
    decoded = "partner.image_1920 = base64.b64encode(img).decode()\n"
    assert "L17" not in _rules(odoo_lint.lint("m/models/m.py", decoded, "20"))
    # addons/printer/models/ir_actions_report.py on 20.0: bytes in a job payload, not a field
    job = 'jobs.append({"type": "zpl", "report": base64.b64encode(self._render(name, ids)[0])})\n'
    assert "L17" not in _rules(odoo_lint.lint("m/models/m.py", job, "20"))
    assert "L17" in _rules(odoo_lint.lint("m/models/m.py", "rec.x_signature_file = base64.b64encode(b)\n", "20"))


def _line_of_rule(findings, rule):
    return next(f.line for f in findings if f.rule == rule)
