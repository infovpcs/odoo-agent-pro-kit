from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .common import Gate

_OPEN_TASK_RE = re.compile(r"^\s*- \[ \]", re.MULTILINE)
_DONE_TASK_RE = re.compile(r"^\s*- \[[xX]\]", re.MULTILINE)


def check_start_coding(module_dir: Optional[Path]) -> Gate:
    if module_dir is None:
        return Gate(ok=True)
    tasks = module_dir / "docs" / "tasks.md"
    if tasks.is_file():
        return _checklist_gate(tasks, module_dir, "/start-coding") or Gate(ok=True)
    return Gate(
        ok=False,
        message=(
            f"/start-coding blocked: PRD files missing for '{module_dir.name}' "
            "(docs/tasks.md not found). Run `/plan-analysis <version> "
            f"{module_dir.name}` to generate requirements.md / design.md / tasks.md / "
            "module_meta.md, then resume /start-coding."
        ),
    )


def _checklist_gate(tasks: Path, module_dir: Path, command: str) -> Optional[Gate]:
    """Block when tasks.md has no `- [ ]` / `- [x]` lines: every later gate would pass vacuously."""
    try:
        text = tasks.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if _OPEN_TASK_RE.search(text) or _DONE_TASK_RE.search(text):
        return None
    return Gate(
        ok=False,
        message=(
            f"{command} blocked: docs/tasks.md for '{module_dir.name}' has no task checklist. "
            "/start-coding ticks tasks off and /testing needs them all done, so write each task "
            "as a `- [ ] Task N: ...` line (re-run `/plan-analysis` or convert the file)."
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
    no_checklist = _checklist_gate(tasks, module_dir, "/testing")
    if no_checklist:
        return no_checklist
    if _OPEN_TASK_RE.search(text):
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: '{module_dir.name}' has incomplete tasks in "
                f"docs/tasks.md. Route to `/start-coding <version> {module_dir.name}` "
                "to finish them first."
            ),
        )
    data = _progress(module_dir)
    if data.get("backend_tests_baseline_parity") and not data.get("backend_tests_passed") \
            and not data.get("backend_tests_baseline"):
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: '{module_dir.name}' claims backend_tests_baseline_parity but "
                "records no backend_tests_baseline (the pre-existing results it is compared "
                "against). Record it in sessions/"
                f"{module_dir.name}_progress.json, or route to `/start-coding`."
            ),
        )
    if not _backend_ok(data):
        return Gate(
            ok=False,
            message=(
                f"/testing blocked: backend tests not confirmed passed for "
                f"'{module_dir.name}' (sessions/{module_dir.name}_progress.json needs "
                "backend_tests_passed = true, or backend_tests_baseline_parity = true with a "
                "backend_tests_baseline). Route to `/start-coding`."
            ),
        )
    return Gate(ok=True)


def _progress(module_dir: Path) -> dict:
    progress = module_dir / "sessions" / f"{module_dir.name}_progress.json"
    try:
        data = json.loads(progress.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _backend_ok(data: dict) -> bool:
    """Passed, or no failure beyond a recorded baseline (migrations keep pre-existing failures)."""
    return bool(data.get("backend_tests_passed")) or bool(
        data.get("backend_tests_baseline_parity") and data.get("backend_tests_baseline"))


def needs_backend_test_record(module_dir: Optional[Path]) -> bool:
    """True when every task is done but no backend-test outcome is recorded for /testing.

    An honest ``backend_tests_passed: false`` counts as recorded; only a missing outcome
    (the /start-coding loop ended without writing it) is flagged.
    """
    if module_dir is None:
        return False
    try:
        text = (module_dir / "docs" / "tasks.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if _OPEN_TASK_RE.search(text) or not _DONE_TASK_RE.search(text):
        return False
    data = _progress(module_dir)
    return "backend_tests_passed" not in data and "backend_tests_baseline_parity" not in data


def needs_ui_check_record(module_dir: Optional[Path]) -> bool:
    """True when a migration target's backend outcome is recorded but no live UI check is.

    Backend parity is necessary but not sufficient for a migration (Phase 11 finding 9: the
    live UI test found seven Odoo 20 bugs that the tests and parity missed). A migration target
    is a module whose progress records ``backend_tests_baseline_parity``. The record is
    ``"ui_check": {"passed": true|false, "result": "<ui-check.py JSON>"}``; an honest failure
    counts as recorded, a result file that does not exist does not.
    """
    if module_dir is None or needs_backend_test_record(module_dir):
        return False
    data = _progress(module_dir)
    if "backend_tests_baseline_parity" not in data:
        return False
    record = data.get("ui_check")
    if not isinstance(record, dict) or not isinstance(record.get("passed"), bool):
        return True
    result = record.get("result")
    if not isinstance(result, str) or not result:
        return True
    path = Path(result)
    return not (path if path.is_absolute() else module_dir / path).is_file()
