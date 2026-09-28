from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_TRUE = {"1", "true", "yes", "on"}

_VERSION_TOKEN_RE = re.compile(r"^(1[789]|20)(\.0)?$")
_MODULE_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]*$")


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


def raw_odoo_allowed() -> bool:
    """True iff the user has explicitly opted in to raw odoo-bin / manage_modules.sh."""
    return os.environ.get("ODOO_KIT_ALLOW_RAW_ODOO", "").strip().lower() in _TRUE


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
        if any((candidate / v).is_dir() for v in ("17.0", "18.0", "19.0", "20.0")):
            return candidate
    # No plan found: an Odoo module, or a repository of modules, is still a gated target, so the
    # gates block (run /plan-analysis) rather than pass because nothing was in scope (Phase 11).
    # Only up to the repository root, so a stray module above the project never matches.
    root = repo_root(current)
    chain = [current, *current.parents] if root else [current]
    for candidate in chain:
        if _is_module(candidate):
            return candidate
        children = _child_modules(candidate)
        if children:
            planned = [child for child in children if (child / "docs" / "tasks.md").is_file()]
            return planned[0] if len(planned) == 1 else candidate
        if candidate == root:
            break
    return None


def _is_module(directory: Path) -> bool:
    return (directory / "__manifest__.py").is_file() or (directory / "__openerp__.py").is_file()


def _child_modules(directory: Path) -> list:
    try:
        return sorted(child for child in directory.iterdir() if child.is_dir() and _is_module(child))
    except OSError:
        return []


def resolve_module_dir(cwd: Optional[Path], prompt_or_args: str) -> Optional[Path]:
    """Resolve the module a command targets, honouring an explicit module argument.

    ``/testing 19 mymod`` run from the *parent* of ``mymod`` must gate ``mymod``,
    not fall through to ``find_module_dir`` (which would return ``None``). Parse
    the tokens: drop a leading ``/command`` token, drop a leading version token
    (``17`` / ``18`` / ``19`` / ``20`` / ``20.0``), and if the next token names an
    existing sub-directory of ``cwd`` use it. Otherwise fall back to
    ``find_module_dir(cwd)``.
    """
    base = (cwd or Path.cwd())
    tokens = (prompt_or_args or "").split()
    if tokens and tokens[0].startswith("/"):
        tokens = tokens[1:]
    if tokens and _VERSION_TOKEN_RE.match(tokens[0]):
        tokens = tokens[1:]
    if tokens and _MODULE_TOKEN_RE.match(tokens[0]):
        candidate = base / tokens[0]
        if candidate.is_dir():
            return candidate.resolve()
    return find_module_dir(base)


def in_odoo_module(cwd: Optional[Path] = None) -> bool:
    return find_module_dir(cwd) is not None


def edit_bodies(tool_input: dict) -> str:
    """All new-content text a Write/Edit/MultiEdit payload would write.

    Returns the top-level ``content`` / ``new_string`` / ``new_str`` when present
    (plain Write / single Edit), otherwise joins every ``edits[i].new_string``
    (MultiEdit) with newlines so scanners and the linter see the edit bodies.
    Shared by the Claude Code dispatcher and the Hermes adapter so the two
    runtimes never drift on MultiEdit payloads.
    """
    direct = tool_input.get("content") or tool_input.get("new_string") or tool_input.get("new_str")
    if direct:
        return direct
    return "\n".join(
        e.get("new_string", "")
        for e in (tool_input.get("edits") or [])
        if isinstance(e, dict)
    )


def _git_stdout(cwd: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def newest_tracked_mtime(cwd: Path) -> float:
    """Newest mtime across all git-tracked files; 0.0 on any error."""
    out = _git_stdout(cwd, "ls-files")
    newest = 0.0
    for rel in out.splitlines():
        try:
            newest = max(newest, (cwd / rel).stat().st_mtime)
        except OSError:
            continue
    return newest
