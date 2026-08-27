from __future__ import annotations

import re
from typing import List, Optional

from .common import Finding

# (rule, compiled regex, {version: severity}, message, fix, applies_to)
#   applies_to: "xml" | "controller" | "model"
_RULES = [
    ("L1", re.compile(r"<tree[\s>/]"),
     {"18": "warn", "19": "block"},
     "<tree> view element", "Replace <tree> with <list>.", "xml"),
    ("L2", re.compile(r"\battrs\s*=|\bstates\s*="),
     {"18": "warn", "19": "block"},
     "attrs=/states= on a view node",
     "Use direct attributes: invisible=, readonly=, required=.", "xml"),
    ("L4", re.compile(r"<group\b[^>]*\b(expand|string)\s*="),
     {"19": "block"},
     "<group expand=/string=> inside a search view",
     "Remove expand/string from <group> in search views.", "xml"),
    ("L5", re.compile(r"name\s*=\s*[\"']category_id[\"']"),
     {"19": "block"},
     "res.groups category_id",
     "Use privilege_id (res.groups.privilege) on Odoo 19.", "xml"),
    ("L3", re.compile(r"type\s*=\s*[\"']json[\"']"),
     {"18": "warn", "19": "block"},
     "type='json' in @http.route",
     "Use type='jsonrpc' on Odoo 18/19.", "controller"),
    ("L6", re.compile(r"_sql_constraints\s*=.*CHECK\s*\(", re.DOTALL),
     {"17": "warn", "18": "warn", "19": "warn"},
     "_sql_constraints CHECK() value rule",
     "Prefer @api.constrains for value validation.", "model"),
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
    return None


def _line_of(content: str, match: re.Match) -> int:
    return content.count("\n", 0, match.start()) + 1


def lint(path: str, content: str, version: Optional[str]) -> List[Finding]:
    kind = _kind(path or "")
    if kind is None:
        return []
    text = content or ""
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
