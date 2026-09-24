from __future__ import annotations

import re
from typing import List, Optional

from .common import Finding

# (rule, compiled regex, {version: severity}, message, fix, applies_to)
#   applies_to: "xml" | "controller" | "model" | "csv"
_RULES = [
    ("L1", re.compile(r"<tree[\s>/]"),
     {"18": "block", "19": "block", "20": "block"},
     "<tree> view element", "Replace <tree> with <list>.", "xml"),
    ("L2", re.compile(r"\battrs\s*=|\bstates\s*="),
     {"18": "warn", "19": "block", "20": "block"},
     "attrs=/states= on a view node",
     "Use direct attributes: invisible=, readonly=, required=.", "xml"),
    ("L4", re.compile(r"<group\b[^>]*\bexpand\s*="),
     {"19": "block", "20": "block"},
     "<group expand=> inside a search view",
     "Remove expand= from <group> in search views (Odoo 19+).", "xml"),
    ("L5", re.compile(r"model\s*=\s*[\"']res\.groups[\"'](?:(?!</record>)[\s\S]){0,400}?name\s*=\s*[\"']category_id[\"']"),
     {"19": "block", "20": "block"},
     "res.groups category_id",
     "Use privilege_id (res.groups.privilege) on Odoo 19+.", "xml"),
    ("L3", re.compile(r"\btype\s*=\s*[\"']json[\"']"),
     {"18": "warn", "19": "block", "20": "block"},
     "type='json' in @http.route",
     "Use type='jsonrpc' on Odoo 18+.", "controller"),
    ("L6", re.compile(r"_sql_constraints\s*=.*?CHECK\s*\(", re.DOTALL),
     {"17": "warn", "18": "warn", "19": "warn", "20": "warn"},
     "_sql_constraints CHECK() value rule",
     "Prefer @api.constrains for value validation.", "model"),
    # Odoo 20 (evidence: odoo/odoo@20.0 d3236ca5c705 — odoo/addons/base/models/ir_access.py,
    # odoo/upgrade_code/19.4-00-ir-access.py, addons/mail_tracking/, web/static/src/libs/materialsymbols)
    ("L7", re.compile(r"\A\s*id\s*,\s*name\s*,\s*model_id[:/]id\b.*perm_read", re.IGNORECASE),
     {"20": "block"},
     "ir.model.access.csv (ACL model removed in Odoo 20)",
     "Convert to security/ir.access.csv (id,name,model_id,group_id/id,operation,domain); "
     "run `odoo-bin upgrade_code --script 19.4-00-ir-access` then review its WARNING/ERROR lines.", "csv"),
    ("L8", re.compile(r"model\s*=\s*[\"']ir\.rule[\"']"),
     {"20": "block"},
     "ir.rule record (record rules removed in Odoo 20)",
     "Move the domain onto an ir.access row (kind permission/restriction); "
     "`odoo-bin upgrade_code --script 19.4-00-ir-access` converts rules + ACLs together.", "xml"),
    ("L9", re.compile(r"[\"']mail\.tracking\.value[\"']|\btracking_value_ids\b"),
     {"20": "warn"},
     "mail.tracking.value / tracking_value_ids (moved out of mail in Odoo 20)",
     "Add 'mail_tracking' to the manifest depends, or stop relying on stored tracking values "
     "(tracking messages are generated on the fly in Odoo 20).", "model"),
    ("L10", re.compile(r"class\s*=\s*[\"'][^\"']*\bfa\s+fa-"),
     {"20": "warn"},
     "Font Awesome icon classes (web client uses Material Symbols in Odoo 20)",
     "Prefer the Material Symbols icon set; Font Awesome is only kept for compatibility.", "xml"),
    ("L11", re.compile(r"name\s*=\s*[\"']toggle_active[\"']|widget\s*=\s*[\"']boolean_button[\"']"),
     {"20": "block"},
     "toggle_active button / boolean_button widget (both removed in Odoo 20)",
     "Drop the stat button; archive via the standard action_archive/action_unarchive "
     "(Action menu) or a web_ribbon on inactive records; use widget=\"boolean_toggle\" if a toggle is needed.", "xml"),
    ("L11", re.compile(r"\.toggle_active\s*\("),
     {"20": "block"},
     "toggle_active() call (BaseModel.toggle_active removed in Odoo 20)",
     "Call action_archive() / action_unarchive() instead.", "model"),
    ("L12", re.compile(r"\bt-esc\s*="),
     {"20": "block"},
     "t-esc in a view arch (forbidden owl directive in Odoo 20 views)",
     "Use t-out; `odoo-bin upgrade_code --script owl3-migration` only rewrites /static/ files, "
     "so fix views/*.xml by hand.", "xml"),
    ("L13", re.compile(r"\bregistry\._init\b"),
     {"20": "block"},
     "Registry._init (private flag removed in Odoo 20; AttributeError at runtime)",
     "Use `not self.env.registry.ready` (or the install_mode/module context keys) instead.", "model"),
]

_ROUTE_XML = ("/views/", "/security/", "/data/", "/report/", "/wizard/")


def _kind(path: str) -> Optional[str]:
    p = "/" + path.replace("\\", "/").lstrip("/")
    if p.endswith(".xml") and any(seg in p for seg in _ROUTE_XML):
        return "xml"
    if p.endswith(".py") and "/controllers/" in p:
        return "controller"
    if p.endswith(".py") and "/models/" in p:
        return "model"
    if p.endswith(".csv") and "/security/" in p:
        return "csv"
    return None


def _line_of(content: str, match: re.Match) -> int:
    return content.count("\n", 0, match.start()) + 1


def _strip_comments(text: str, kind: str) -> str:
    if kind == "xml":
        return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)
    if kind == "csv":
        return text
    # controller / model: blank everything from the first '#' on each line
    out = []
    for ln in text.split("\n"):
        h = ln.find("#")
        out.append(ln if h == -1 else ln[:h])
    return "\n".join(out)


def lint(path: str, content: str, version: Optional[str]) -> List[Finding]:
    kind = _kind(path or "")
    if kind is None:
        return []
    text = _strip_comments(content or "", kind)
    out: List[Finding] = []
    for rule, rx, sev_map, message, fix, applies in _RULES:
        if applies != kind:
            continue
        m = rx.search(text)
        if not m:
            continue
        if version is None:
            severity = "warn"
        else:
            severity = sev_map.get(version)
            if severity is None:
                continue
        out.append(Finding(severity=severity, rule=rule, line=_line_of(text, m),
                            message=message, fix=fix))
    return out
