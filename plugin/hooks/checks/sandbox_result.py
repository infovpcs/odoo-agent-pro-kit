from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from .common import OperationResult, repo_root

_CMD_RE = re.compile(
    r"\b(?:sandboxctl\s+module\s+(?P<session>\S+)|bash\s+(?:\./)?manage_modules\.sh)\s+"
    r"(?P<op>install|update|test)\s+(?P<module>[a-z][a-z0-9_]*)",
)


def _sandbox_roots(cwd: Path) -> list[Path]:
    """Directories that may contain a ``.sandbox/`` tree, most specific first.

    Agents often edit a module that lives *outside* the kit repo (e.g. a
    separate ``vpcs_apps_cloud_18`` checkout) and rsync it into the session,
    so ``.sandbox/`` is not always an ancestor of ``cwd``. ``ODOO_KIT_SANDBOX_ROOT``
    lets such a session point back at the kit checkout.
    """
    roots: list[Path] = []
    kit = os.environ.get("ODOO_KIT_SANDBOX_ROOT")
    if kit:
        roots.append(Path(kit).expanduser())
    start = cwd.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".sandbox").is_dir():
            roots.append(candidate)
            break
    return roots


def _results_dir(cwd: Path, session: Optional[str] = None) -> Optional[Path]:
    env = os.environ.get("ODOO_RESULTS_DIR")
    if env:
        return Path(env)
    start = cwd.resolve()

    for root in _sandbox_roots(cwd):
        sessions_dir = root / ".sandbox" / "sessions"
        # 1. session id named on the command line (`sandboxctl module <session> …`)
        if session:
            cand = sessions_dir / session / "results"
            if cand.is_dir():
                return cand
        # 2. active session recorded in .sandbox/session.json
        sj = root / ".sandbox" / "session.json"
        if sj.is_file():
            try:
                data = json.loads(sj.read_text(encoding="utf-8"))
                sid = data.get("session_id") if isinstance(data, dict) else None
            except (OSError, ValueError, AttributeError, TypeError):
                sid = None
            if sid:
                cand = (repo_root(start) or root) / ".sandbox" / "sessions" / sid / "results"
                if cand.is_dir():
                    return cand
        # 3. newest session directory that actually has a results/ folder
        if sessions_dir.is_dir():
            for s in sorted(sessions_dir.iterdir(),
                            key=lambda p: p.stat().st_mtime, reverse=True):
                if (s / "results").is_dir():
                    return s / "results"

    return start / "logs" / "test_results"


def read_operation_result(bash_command: str, cwd: Path) -> Optional[OperationResult]:
    m = _CMD_RE.search(bash_command or "")
    if not m:
        return None
    operation, module = m.group("op"), m.group("module")
    rdir = _results_dir(Path(cwd), m.group("session"))
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
