#!/usr/bin/env python3
"""Claude Code hook dispatcher for odoo-agent-pro-kit.

Usage: odoo_hook.py <Event>   (reads a JSON payload on stdin)
Exit 0 = allow, 2 = block (reason on stderr). Fails open on any error.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # plugin/hooks on path

from checks import (  # noqa: E402
    authz,
    common,
    gates,
    guard,
    odoo_lint,
    paths,
    sandbox_result,
    version,
)


def _cwd(payload: dict) -> Path:
    return Path(payload.get("cwd") or os.getcwd())


def _tool_input(payload: dict) -> dict:
    return payload.get("tool_input") or payload.get("tool_response") or {}


def _handle_session_start(payload: dict) -> int:
    cwd = _cwd(payload)
    mod = common.find_module_dir(cwd)
    v = version.detect_odoo_version(cwd)
    bits = []
    if v:
        bits.append(f"Odoo {v}.0 workspace")
    if mod is not None:
        g_sc = gates.check_start_coding(mod)
        g_t = gates.check_testing(mod)
        bits.append(f"module '{mod.name}'")
        bits.append("tasks.md present" if g_sc.ok else "no tasks.md (run /plan-analysis)")
        bits.append("ready for /testing" if g_t.ok else "not yet ready for /testing")
    if bits:
        print("[odoo-agent-pro-kit] " + " | ".join(bits))
    return 0


def _handle_user_prompt(payload: dict) -> int:
    prompt = (payload.get("prompt") or "").strip()
    mod = common.resolve_module_dir(_cwd(payload), prompt)
    if prompt.startswith("/start-coding"):
        g = gates.check_start_coding(mod)
    elif prompt.startswith("/testing"):
        g = gates.check_testing(mod)
    else:
        return 0
    if not g.ok:
        print(g.message, file=sys.stderr)
        return 2
    return 0


def _handle_pre_tool(payload: dict) -> int:
    tool = payload.get("tool_name") or ""
    ti = _tool_input(payload)
    cwd = _cwd(payload)
    if tool == "Bash":
        vs = guard.classify_bash(ti.get("command", ""),
                                 vcs_allowed=authz.vcs_write_allowed(cwd),
                                 raw_allowed=common.raw_odoo_allowed())
        if vs:
            for v in vs:
                print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}", file=sys.stderr)
            return 2
    elif tool in ("Write", "Edit", "MultiEdit"):
        root = common.repo_root(cwd)
        if root is not None:
            content = common.edit_bodies(ti) or None
            vs = paths.scan_write(ti.get("file_path", ""), content, root)
            if vs:
                for v in vs:
                    print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}", file=sys.stderr)
                return 2
    return 0


def _handle_post_tool(payload: dict) -> int:
    tool = payload.get("tool_name") or ""
    ti = _tool_input(payload)
    cwd = _cwd(payload)
    if tool in ("Write", "Edit", "MultiEdit"):
        fp = ti.get("file_path", "")
        content = common.edit_bodies(ti)
        findings = odoo_lint.lint(fp, content, version.detect_odoo_version(cwd))
        blockers = [f for f in findings if f.severity == "block"]
        warns = [f for f in findings if f.severity == "warn"]
        if blockers:
            for f in blockers:
                print(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}", file=sys.stderr)
            return 2
        for f in warns:
            print(f"[odoo {f.rule}] line {f.line}: {f.message} -> {f.fix}")
    elif tool == "Bash":
        res = sandbox_result.read_operation_result(ti.get("command", ""), cwd)
        if res is not None and not res.module_state_ok:
            print(f"[odoo-agent-pro-kit] sandbox operation status={res.status} "
                  f"({res.reason or 'see result'}). Do NOT mark the task complete. "
                  f"Result: {res.result_path}")
    return 0


def _handle_stop(payload: dict) -> int:
    if payload.get("stop_hook_active"):
        return 0
    # Advisory only: mirror contributor_hook.py — remind about validate.sh only
    # when a stamp EXISTS and is stale (older than the newest tracked file). An
    # absent stamp means the mechanism is not in use here; do not nag.
    root = common.repo_root(_cwd(payload))
    if root is None:
        return 0
    stamp = root / ".git" / "odoo-kit-validate.stamp"
    if stamp.is_file() and common.newest_tracked_mtime(root) > stamp.stat().st_mtime:
        print("[odoo-agent-pro-kit] Reminder: ./scripts/validate.sh has not run since the "
              "last tracked change — run it from a clean shell before committing a phase.")
    return 0


def _handle_session_end(payload: dict) -> int:
    del payload  # unused — SessionEnd cleanup needs no payload fields
    plugin_dir = Path(__file__).resolve().parent.parent
    pid_dir = plugin_dir / "odoo_mcp"
    if pid_dir.is_dir():
        for pid_file in pid_dir.glob("mcp_server_*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 15)
            except (OSError, ValueError):
                pass
            try:
                pid_file.unlink()
            except OSError:
                pass
    return 0


_HANDLERS = {
    "SessionStart": _handle_session_start,
    "UserPromptSubmit": _handle_user_prompt,
    "PreToolUse": _handle_pre_tool,
    "PostToolUse": _handle_post_tool,
    "Stop": _handle_stop,
    "SessionEnd": _handle_session_end,
}


def main(argv: list[str], stdin_text: str) -> int:
    try:
        event = argv[0] if argv else ""
        try:
            payload = json.loads(stdin_text) if stdin_text.strip() else {}
        except ValueError:
            return 0
        if not isinstance(payload, dict):
            return 0
        if common.hooks_disabled():
            return 0
        if event not in _HANDLERS:
            return 0
        if event not in ("SessionStart", "SessionEnd"):
            cwd = _cwd(payload)
            in_scope = common.in_odoo_module(cwd)
            if not in_scope and event == "UserPromptSubmit":
                # A slash command can name a module that lives *below* cwd
                # (e.g. `/testing 19 mymod` run from the workspace root).
                in_scope = common.resolve_module_dir(cwd, payload.get("prompt") or "") is not None
            if not in_scope:
                return 0
        return _HANDLERS[event](payload)
    except Exception as exc:  # noqa: BLE001 - fail open
        print(f"[odoo-agent-pro-kit] hook error (ignored): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    try:
        _stdin = sys.stdin.read()
    except Exception:  # noqa: BLE001 - fail open even on a stdin read failure
        sys.exit(0)
    sys.exit(main(sys.argv[1:], _stdin))
