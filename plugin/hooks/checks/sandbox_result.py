from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from .common import OperationResult, repo_root

_CMD_RE = re.compile(
    r"\b(?:sandboxctl\s+module\s+\S+|bash\s+(?:\./)?manage_modules\.sh)\s+"
    r"(?P<op>install|update|test)\s+(?P<module>[a-z][a-z0-9_]*)",
)


def _results_dir(cwd: Path) -> Optional[Path]:
    env = os.environ.get("ODOO_RESULTS_DIR")
    if env:
        return Path(env)
    start = cwd.resolve()
    for candidate in (start, *start.parents):
        session = candidate / ".sandbox" / "session.json"
        if session.is_file():
            try:
                data = json.loads(session.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    sid = data.get("session_id")
                else:
                    sid = None
            except (OSError, ValueError, AttributeError, TypeError):
                sid = None
            root = repo_root(start) or candidate
            if sid:
                return root / ".sandbox" / "sessions" / sid / "results"
            break
    return start / "logs" / "test_results"


def read_operation_result(bash_command: str, cwd: Path) -> Optional[OperationResult]:
    m = _CMD_RE.search(bash_command or "")
    if not m:
        return None
    operation, module = m.group("op"), m.group("module")
    rdir = _results_dir(Path(cwd))
    if rdir is None or not rdir.is_dir():
        return None

    candidates = sorted(rdir.glob(f"{operation}-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("module") not in (module, None):
            continue
        status = str(data.get("status", "unknown"))
        err = data.get("error")
        reason = data.get("message") or (err or {}).get("summary") or ""
        return OperationResult(
            status=status,
            module_state_ok=(status == "succeeded" and err is None),
            reason=reason,
            result_path=str(path.resolve()),
        )
    return None
