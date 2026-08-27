from __future__ import annotations
from plugin.hooks.checks import odoo_lint


def _rules(findings):
    return sorted(f.rule for f in findings)


def _sev(findings, rule):
    return next(f.severity for f in findings if f.rule == rule)


def test_l1_tree_blocks_on_19():
    xml = '<odoo>\n<record><field name="arch"><list/></field></record>\n<tree/>\n</odoo>'
    f = odoo_lint.lint("mymod/views/x.xml", xml, "19")
    assert "L1" in _rules(f) and _sev(f, "L1") == "block"


def test_l1_tree_blocks_on_18():
    # Recent Odoo 18 builds removed <tree> entirely (hard ParseError), so L1
    # is block-severity for 18 as well as 19.
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", "18")
    assert _sev(f, "L1") == "block"


def test_l1_tree_ok_on_17():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", "17")
    assert "L1" not in _rules(f)


def test_l3_type_json_blocks_on_19():
    py = "@http.route('/x', type='json', auth='user')\ndef x(self): pass\n"
    f = odoo_lint.lint("mymod/controllers/main.py", py, "19")
    assert "L3" in _rules(f) and _sev(f, "L3") == "block"


def test_l2_attrs_blocks_on_19():
    f = odoo_lint.lint("mymod/views/v.xml", '<field name="x" attrs="{\'invisible\': True}"/>', "19")
    assert "L2" in _rules(f) and _sev(f, "L2") == "block"


def test_l5_category_id_blocks_on_19():
    xml = '<record model="res.groups"><field name="category_id" ref="base.module_category_x"/></record>'
    f = odoo_lint.lint("mymod/security/groups.xml", xml, "19")
    assert "L5" in _rules(f) and _sev(f, "L5") == "block"


def test_none_version_only_warns():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", None)
    assert all(x.severity == "warn" for x in f)


def test_clean_file_no_findings():
    f = odoo_lint.lint("mymod/models/m.py", "class M(models.Model):\n    _name = 'm'\n", "19")
    assert f == []


def test_l4_form_group_string_not_flagged():
    f = odoo_lint.lint("mymod/views/v.xml", '<group string="General Information"><field name="x"/></group>', "19")
    assert "L4" not in _rules(f)


def test_l4_search_group_expand_blocked():
    f = odoo_lint.lint("mymod/views/v.xml", '<search><group expand="0"><filter name="f"/></group></search>', "19")
    assert "L4" in _rules(f) and _sev(f, "L4") == "block"


def test_l5_partner_category_field_not_flagged():
    f = odoo_lint.lint("mymod/views/partner.xml", '<field name="category_id" widget="many2many_tags"/>', "19")
    assert "L5" not in _rules(f)


def test_l5_res_groups_category_blocked():
    xml = '<record id="g" model="res.groups"><field name="name">X</field><field name="category_id" ref="base.module_category_x"/></record>'
    f = odoo_lint.lint("mymod/security/groups.xml", xml, "19")
    assert "L5" in _rules(f) and _sev(f, "L5") == "block"


def test_comment_not_flagged_xml():
    f = odoo_lint.lint("mymod/views/v.xml", '<!-- legacy <tree/> removed -->\n<list/>', "19")
    assert f == []


def test_comment_not_flagged_py():
    py = "# was type='json' before\n@http.route('/x', type='jsonrpc')\ndef x(self): pass"
    f = odoo_lint.lint("mymod/controllers/main.py", py, "19")
    assert f == []


def test_line_number_reported():
    xml = "<odoo>\n<data>\n<tree/>\n</data>\n</odoo>"
    f = odoo_lint.lint("mymod/views/x.xml", xml, "19")
    assert _sev(f, "L1") == "block"
    assert next(x.line for x in f if x.rule == "L1") == 3
