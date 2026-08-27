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


def test_l1_tree_warns_on_18():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", "18")
    assert _sev(f, "L1") == "warn"


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
    f = odoo_lint.lint("mymod/security/groups.xml", '<field name="category_id" ref="base.module_category_x"/>', "19")
    assert "L5" in _rules(f) and _sev(f, "L5") == "block"


def test_none_version_only_warns():
    f = odoo_lint.lint("mymod/views/x.xml", "<tree/>", None)
    assert all(x.severity == "warn" for x in f)


def test_clean_file_no_findings():
    f = odoo_lint.lint("mymod/models/m.py", "class M(models.Model):\n    _name = 'm'\n", "19")
    assert f == []
