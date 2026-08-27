from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from .common import find_module_dir

_META_RE = re.compile(r"(?:odoo[_ ]?version|version)\s*[:=]\s*\"?(1[789])", re.IGNORECASE)


def _norm(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    m = re.match(r"\s*(1[789])", str(raw))
    return m.group(1) if m else None


def detect_odoo_version(cwd: Optional[Path] = None) -> Optional[str]:
    start = (cwd or Path.cwd()).resolve()

    for candidate in (start, *start.parents):
        session = candidate / ".sandbox" / "session.json"
        if session.is_file():
            try:
                data = json.loads(session.read_text(encoding="utf-8"))
                v = _norm(data.get("odoo_version"))
                if v:
                    return v
            except (OSError, ValueError):
                pass
            break

    module_dir = find_module_dir(start)
    if module_dir is not None:
        for v in ("19", "18", "17"):
            if (module_dir / f"{v}.0").is_dir() or (module_dir.parent / f"{v}.0").is_dir():
                return v
        meta = module_dir / "docs" / "module_meta.md"
        if meta.is_file():
            try:
                m = _META_RE.search(meta.read_text(encoding="utf-8", errors="replace"))
                if m:
                    return m.group(1)
            except OSError:
                pass

    return _norm(os.environ.get("DEFAULT_ODOO_VERSION"))
