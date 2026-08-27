from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_TRUE = {"1", "true", "yes", "on"}


@dataclass
class Finding:
    severity: str  # "block" | "warn"
    rule: str
    line: int
    message: str
    fix: str


@dataclass
class Violation:
    kind: str
    message: str
    lift_hint: str = ""


@dataclass
class Gate:
    ok: bool
    message: str = ""


@dataclass
class OperationResult:
    status: str
    module_state_ok: bool
    reason: str
    result_path: str


def hooks_disabled() -> bool:
    return os.environ.get("ODOO_KIT_HOOKS_DISABLED", "").strip().lower() in _TRUE


def repo_root(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def find_module_dir(start: Optional[Path] = None) -> Optional[Path]:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "docs" / "tasks.md").is_file():
            return candidate
    for candidate in (current, *current.parents):
        if any((candidate / v).is_dir() for v in ("17.0", "18.0", "19.0")):
            return candidate
    return None


def in_odoo_module(cwd: Optional[Path] = None) -> bool:
    return find_module_dir(cwd) is not None
