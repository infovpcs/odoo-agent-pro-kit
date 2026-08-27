#!/usr/bin/env python3
"""Repo-contributor Claude Code hook for odoo-agent-pro-kit.

Enforces the AGENTS.md phase-workflow rules. Referenced from the repo-root
.claude/settings.json (not shipped in the plugin package).
Usage: contributor_hook.py <Event>   (JSON payload on stdin)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugin" / "hooks"))
from checks import guard  # noqa: E402

_TRUE = {"1", "true", "yes", "on"}
_CODE_SUFFIXES = (".py", ".sh", ".json", ".yaml", ".yml")
_PHASE_DOCS = ("docs/docker-sandbox/tasks.md", "SESSION_CONTEXT.md", "README.md")


def _cwd(payload: dict) -> Path:
    return Path(payload.get("cwd") or os.getcwd())


def _phase_authorized() -> bool:
    return os.environ.get("AGENTS_PHASE_AUTHORIZED", "").strip().lower() in _TRUE


def _git(cwd: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _handle_session_start(payload: dict) -> int:
    cwd = _cwd(payload)
    sc = cwd / "SESSION_CONTEXT.md"
    if sc.is_file():
        lines = sc.read_text(encoding="utf-8", errors="replace").splitlines()
        try:
            start = next(i for i, ln in enumerate(lines) if ln.strip().lower().startswith("## current state"))
            print("\n".join(lines[start:start + 40]))
        except StopIteration:
            pass
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(cwd, "status", "-s")
    if branch:
        print(f"\n[branch] {branch}")
    if status:
        print(f"[uncommitted]\n{status}")
    return 0


def _newest_tracked_mtime(cwd: Path) -> float:
    out = _git(cwd, "ls-files")
    newest = 0.0
    for rel in out.splitlines():
        p = cwd / rel
        try:
            newest = max(newest, p.stat().st_mtime)
        except OSError:
            continue
    return newest


def _handle_pre_tool(payload: dict) -> int:
    if (payload.get("tool_name") or "") != "Bash":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "")
    cwd = _cwd(payload)

    for v in guard.classify_bash(cmd, vcs_allowed=_phase_authorized()):
        if v.kind in ("vcs_write", "destructive_cleanup"):
            print(f"[BLOCKED] {v.message}\n  -> {v.lift_hint}\n  (set AGENTS_PHASE_AUTHORIZED=1 "
                  "after the user approves)", file=sys.stderr)
            return 2

    import re
    if re.search(r"\bgit\s+commit\b", cmd) and "--amend" not in cmd:
        stamp = cwd / ".git" / "odoo-kit-validate.stamp"
        stamp_mtime = stamp.stat().st_mtime if stamp.is_file() else 0.0
        if _newest_tracked_mtime(cwd) > stamp_mtime:
            print("[BLOCKED] ./scripts/validate.sh has not run since the last tracked change.\n"
                  "  -> Run it from a clean shell, then `touch .git/odoo-kit-validate.stamp`.",
                  file=sys.stderr)
            return 2
    return 0


def _handle_stop(payload: dict) -> int:
    cwd = _cwd(payload)
    status = _git(cwd, "status", "-s")
    changed = [ln[3:] for ln in status.splitlines() if ln[3:].strip()]
    code_changed = any(c.endswith(_CODE_SUFFIXES) for c in changed)
    docs_changed = any(any(c.endswith(d) or c == d for d in _PHASE_DOCS) for c in changed)
    if code_changed and not docs_changed:
        print("[odoo-agent-pro-kit] Reminder: update docs/docker-sandbox/tasks.md, "
              "SESSION_CONTEXT.md, and README.md alongside code changes (AGENTS.md rule 4).")
    return 0


_HANDLERS = {
    "SessionStart": _handle_session_start,
    "PreToolUse": _handle_pre_tool,
    "Stop": _handle_stop,
}


def main(argv: list[str], stdin_text: str) -> int:
    try:
        event = argv[0] if argv else ""
        try:
            payload = json.loads(stdin_text) if stdin_text.strip() else {}
        except ValueError:
            return 0
        if os.environ.get("ODOO_KIT_HOOKS_DISABLED", "").strip().lower() in _TRUE:
            return 0
        if not isinstance(payload, dict) or event not in _HANDLERS:
            return 0
        return _HANDLERS[event](payload)
    except Exception as exc:  # noqa: BLE001 - fail open
        print(f"[odoo-agent-pro-kit] contributor hook error (ignored): {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.read()))
