from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .common import repo_root

_TRUE = {"1", "true", "yes", "on"}


def vcs_write_allowed(cwd: Optional[Path] = None) -> bool:
    if os.environ.get("ODOO_KIT_ALLOW_VCS_WRITE", "").strip().lower() in _TRUE:
        return True
    start = (cwd or Path.cwd()).resolve()
    candidates = [start / ".sandbox" / "AUTHORIZED"]
    root = repo_root(start)
    if root is not None:
        candidates.append(root / ".sandbox" / "AUTHORIZED")
    return any(c.is_file() for c in candidates)
