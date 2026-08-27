from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .common import Gate

_OPEN_TASK_RE = re.compile(r"^\s*- \[ \]", re.MULTILINE)


def check_start_coding(module_dir: Optional[Path]) -> Gate:
    if module_dir is None:
        return Gate(ok=True)
    if (module_dir / "docs" / "tasks.md").is_file():
        return Gate(ok=True)
    return Gate(
        ok=False,
        message=(
            f"/start-coding blocked: PRD files missing for '{module_dir.name}' "
            "(docs/tasks.md not found). Run `/plan-analysis <version> "
            f"{module_dir.name}` to generate requirements.md / design.md / tasks.md / "
            "module_meta.md, then resume /start-coding."
        ),
    )


def check_testing(module_dir: Optional[Path]) -> Gate:
    if module_dir is None:
        return Gate(ok=True)
    tasks = module_dir / "docs" / "tasks.md"
    if not tasks.is_file():
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: docs/tasks.md not found for '{module_dir.name}'. "
                f"Run `/start-coding <version> {module_dir.name}` first."
            ),
        )
    try:
        text = tasks.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return Gate(ok=True)
    if _OPEN_TASK_RE.search(text):
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: '{module_dir.name}' has incomplete tasks in "
                f"docs/tasks.md. Route to `/start-coding <version> {module_dir.name}` "
                "to finish them first."
            ),
        )
    progress = module_dir / "sessions" / f"{module_dir.name}_progress.json"
    passed = False
    if progress.is_file():
        try:
            data = json.loads(progress.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                passed = bool(data.get("backend_tests_passed"))
        except (OSError, ValueError):
            passed = False
    if not passed:
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: backend tests not confirmed passed for "
                f"'{module_dir.name}' (sessions/{module_dir.name}_progress.json "
                "backend_tests_passed != true). Route to `/start-coding`."
            ),
        )
    return Gate(ok=True)
