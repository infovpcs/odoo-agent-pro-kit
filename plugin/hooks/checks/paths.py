from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import List, Optional

from .common import Violation

_ENT_PATH_RE = re.compile(r"(^|/)(ent-1[789]|enterprise|web_studio)(/|$)")
_ENT_CONTENT_RE = re.compile(r"OEEL-1|OPL-1|Odoo Enterprise Edition License")
_SECRET_RES = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    re.compile(r"ghp_[0-9A-Za-z]{36}"),
]
_ENV_LINE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Za-z0-9_]*)\s*=\s*(\S.*)$",
    re.MULTILINE,
)
_DENYLIST = Path(__file__).with_name("customer_denylist.txt")


def _load_denylist() -> List[str]:
    if not _DENYLIST.is_file():
        return []
    out = []
    for line in _DENYLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def scan_write(target_path: str, content: Optional[str], repo_root: Path) -> List[Violation]:
    out: List[Violation] = []
    try:
        target = Path(target_path).resolve()
        root = Path(repo_root).resolve()
    except (OSError, RuntimeError):
        return out

    try:
        rel = target.relative_to(root)
    except ValueError:
        return out  # not inside the repo — not our concern

    rel_str = str(rel)
    body = content or ""
    name = target.name.lower()
    is_sample = name.endswith((".example", ".sample", ".template")) or ".env.example" in name

    if _ENT_PATH_RE.search("/" + rel_str) or _ENT_CONTENT_RE.search(body):
        out.append(Violation(
            kind="enterprise_source",
            message=f"Refusing to write licensed Odoo Enterprise material into the repo: {rel_str}",
            lift_hint="Keep Enterprise source in your licensed clone (e.g. ~/workspace/ent-19), never in this repo.",
        ))

    if not is_sample:
        if any(rx.search(body) for rx in _SECRET_RES):
            out.append(Violation(
                kind="secret_material",
                message=f"Refusing to write secret material into the repo: {rel_str}",
                lift_hint="Put credentials in a .env outside any git repo (e.g. ~/.hermes/.env, chmod 600).",
            ))
        elif _ENV_LINE_RE.search(body):
            out.append(Violation(
                kind="secret_material",
                message=f"Refusing to write a populated secret env var into the repo: {rel_str}",
                lift_hint="Use a *.env.example with empty values; keep real values outside the repo.",
            ))

    for pattern in _load_denylist():
        if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch("/" + rel_str, pattern):
            out.append(Violation(
                kind="customer_data",
                message=f"Path matches the customer-data deny-list: {rel_str}",
                lift_hint="Client source/data must not be committed to this pipeline repo.",
            ))
            break

    return out
