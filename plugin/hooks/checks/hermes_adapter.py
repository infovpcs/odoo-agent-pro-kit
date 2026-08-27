"""Hermes-runtime adapter over the shared plugin/hooks/checks/ library.

Gives a Hermes session the same guard/lint/gate behaviour that the Claude Code
dispatcher (plugin/hooks/odoo_hook.py) provides. Every function here is a thin
translation layer: the actual policy lives in the checks/ modules and is shared
with the Claude Code side, so the two runtimes never drift.

Python stdlib only.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from . import authz, common, gates, guard, odoo_lint, paths, sandbox_result, version


def _cwd(cwd) -> Path:
    return Path(cwd) if cwd else Path.cwd()


def pre_tool_call_directive(tool_name: str, tool_args: dict, cwd) -> Optional[dict]:
    """Return a Hermes ``pre_tool_call`` block directive, or ``None`` to allow.

    IMPORTANT: the directive shape ``{"decision": "block", "reason": <text>}`` is
    the ONE place the Hermes contract is encoded. It is assumed from the
    NousResearch/hermes-agent docs and MUST be verified against the installed
    Hermes version (see Task 13 open item). If the real key names differ, change
    them here only -- nothing else in the plugin depends on the shape.
    """
    if common.hooks_disabled():
        return None
    c = _cwd(cwd)
    if not common.in_odoo_module(c):
        return None
    args = tool_args or {}
    reasons: List[str] = []
    if tool_name in ("Bash", "shell", "run_shell"):
        for v in guard.classify_bash(args.get("command", ""), vcs_allowed=authz.vcs_write_allowed(c)):
            reasons.append(f"{v.message} -> {v.lift_hint}")
    elif tool_name in ("Write", "Edit", "write_file", "edit_file"):
        root = common.repo_root(c)
        if root is not None:
            content = args.get("content") or args.get("new_string") or args.get("new_str")
            for v in paths.scan_write(args.get("file_path") or args.get("path", ""), content, root):
                reasons.append(f"{v.message} -> {v.lift_hint}")
    if reasons:
        return {"decision": "block", "reason": "\n".join(reasons)}
    return None


def post_tool_call_notes(tool_name: str, tool_args: dict, cwd) -> List[str]:
    """Advisory strings for Hermes ``post_tool_call`` (observe only, cannot block)."""
    if common.hooks_disabled():
        return []
    c = _cwd(cwd)
    if not common.in_odoo_module(c):
        return []
    args = tool_args or {}
    notes: List[str] = []
    if tool_name in ("Write", "Edit", "write_file", "edit_file"):
        fp = args.get("file_path") or args.get("path", "")
        content = args.get("content") or args.get("new_string") or args.get("new_str") or ""
        for f in odoo_lint.lint(fp, content, version.detect_odoo_version(c)):
            notes.append(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}")
    elif tool_name in ("Bash", "shell", "run_shell"):
        res = sandbox_result.read_operation_result(args.get("command", ""), c)
        if res is not None and not res.module_state_ok:
            notes.append(f"sandbox operation status={res.status} ({res.reason or 'see result'}); "
                         f"do not mark the task complete. Result: {res.result_path}")
    return notes


def session_start_lines(cwd) -> List[str]:
    """The same workspace summary the Claude Code session-start handler prints."""
    c = _cwd(cwd)
    mod = common.find_module_dir(c)
    v = version.detect_odoo_version(c)
    out: List[str] = []
    if v:
        out.append(f"Odoo {v}.0 workspace detected")
    if mod is not None:
        out.append(f"module '{mod.name}': "
                   + ("tasks.md present" if gates.check_start_coding(mod).ok else "no tasks.md")
                   + ", "
                   + ("ready for /testing" if gates.check_testing(mod).ok else "not ready for /testing"))
    return out


def command_gate(command: str, prompt: str, cwd) -> Optional[str]:
    """Return a redirect message when a command's prerequisite gate fails, else ``None``."""
    if common.hooks_disabled():
        return None
    mod = common.find_module_dir(_cwd(cwd))
    if command == "start-coding":
        g = gates.check_start_coding(mod)
    elif command == "testing":
        g = gates.check_testing(mod)
    else:
        return None
    return None if g.ok else g.message
