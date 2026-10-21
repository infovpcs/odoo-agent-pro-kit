"""
Dynamic context-usage handoff guard for odoo-agent-pro-kit.

Fires on the ``post_api_request`` Hermes plugin hook (real per-turn token
usage, not a guess) and, once context usage crosses a threshold, writes the
episodic-context handoff files (CLAUDE.md / GEMINI.md / AGENTS.md) via the
existing CommandingSystem/auto_test/context_writer.py contract, then injects
a message telling the agent to wrap up the current step and hand off to a
fresh session.

This is deliberately command-agnostic: it fires for /plan-analysis,
/start-coding, /testing, /fleet, or any other in-progress work — not just a
hardcoded phase — because context pressure depends on module complexity and
how much the running command has already done, not on which command it is.

Threshold is dynamic, not a single fixed 60%:
- Base threshold: ``context_handoff.threshold_pct`` plugin config, default 0.60.
- Auto-tightened for larger modules (more docs/tasks.md tasks means less
  headroom per remaining task): see ``_effective_threshold_pct``.
- Re-fires only when usage grows by another full bucket (default 10 points)
  past the last trigger, so a long-running command isn't spammed every turn
  once past threshold.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).parent
_CONTEXT_WRITER = _PLUGIN_DIR / "skills" / "CommandingSystem" / "auto_test" / "context_writer.py"

_DEFAULT_THRESHOLD_PCT = 0.60
_DEFAULT_CONTEXT_WINDOW_TOKENS = 128_000
_RETRIGGER_BUCKET_PCT = 0.10

# module_dir (as string) -> last usage_pct bucket that triggered a handoff,
# so a long single-process session doesn't rewrite CLAUDE.md every API call
# once past threshold. Reset per plugin-process lifetime (matches
# _discovery_by_version's own process-lifetime cache pattern in __init__.py).
_last_triggered_bucket: dict[str, float] = {}


_MARKER_RE = re.compile(r"^\[odoo-kit-command\] name=(\S+) version=(\S+) args=(.*)$", re.M)


def parse_command_marker(text: Any) -> Optional[dict]:
    """The kit command named by the last marker line in ``text`` (see ``_command_prompt``)."""
    if isinstance(text, list):
        text = "\n".join(p.get("text", "") for p in text if isinstance(p, dict))
    if not isinstance(text, str):
        return None
    matches = _MARKER_RE.findall(text)
    if not matches:
        return None
    name, version, args = matches[-1]
    args = args.strip()
    return {
        "name": name,
        "version": None if version == "-" else version,
        "args": None if args in ("", "-") else args,
    }


def _find_module_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from ``start`` (default cwd) looking for docs/tasks.md.

    Mirrors the detection the PreCompact shell hook (save_progress.sh) and
    context_handoff_workflow.md already use: a module directory is one that
    has docs/tasks.md, i.e. /plan-analysis has already run there.
    """
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "docs" / "tasks.md").is_file():
            return candidate
    return None


def _count_tasks(tasks_md: Path) -> tuple[int, int]:
    text = tasks_md.read_text(encoding="utf-8", errors="replace")
    total = len(re.findall(r"^- \[[ xX]\]", text, re.MULTILINE))
    done = len(re.findall(r"^- \[[xX]\]", text, re.MULTILINE))
    return done, total


def _effective_threshold_pct(base_pct: float, tasks_total: int) -> float:
    """Scale the handoff threshold down for larger/more complex modules.

    A module with many remaining tasks needs more headroom per task, so it
    should hand off earlier (lower threshold) than a two-task module that can
    safely run closer to the limit. Bounds keep this within a sane range
    regardless of config.
    """
    if tasks_total <= 5:
        adjustment = 0.05
    elif tasks_total <= 15:
        adjustment = 0.0
    else:
        adjustment = -0.10
    return max(0.40, min(0.80, base_pct + adjustment))


def _usage_pct(usage: Optional[dict], context_window_tokens: int) -> Optional[float]:
    if not usage or not context_window_tokens:
        return None
    total = usage.get("total_tokens")
    if not isinstance(total, (int, float)) or total <= 0:
        return None
    return float(total) / float(context_window_tokens)


def _module_version(module_dir: Path) -> str:
    for meta_name in ("module_meta.md",):
        meta = module_dir / "docs" / meta_name
        if meta.is_file():
            match = re.search(r"(?:odoo[_ ]?version|version)\s*[:=]\s*\"?(1[789]|20)(?!\d)", meta.read_text(errors="replace"), re.IGNORECASE)
            if match:
                return match.group(1)
    for version_dir in ("19.0", "18.0", "17.0"):
        if (module_dir.parent / version_dir).is_dir() or (module_dir / version_dir).is_dir():
            return version_dir.split(".")[0]
    return "19"


def _write_handoff(module_dir: Path, usage_pct: float, threshold_pct: float, triggered_by: str) -> bool:
    if not _CONTEXT_WRITER.is_file():
        logger.warning(
            "[odoo-agent-pro-kit] context handoff triggered but writer script missing at %s",
            _CONTEXT_WRITER,
        )
        return False

    tasks_md = module_dir / "docs" / "tasks.md"
    tasks_done, tasks_total = _count_tasks(tasks_md) if tasks_md.is_file() else (0, 0)
    version = _module_version(module_dir)
    now_iso = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # context_writer.py only accepts flat CLI args for the fields it persists
    # under session_data["extra"]; the dynamic-handoff marker itself is
    # written via a direct import instead of shelling out a second time, so
    # this call also carries the tasks/summary snapshot in one pass.
    sys.path.insert(0, str(_CONTEXT_WRITER.parent))
    try:
        import context_writer  # type: ignore[import-not-found]

        context_writer.write_context(
            module_dir=module_dir,
            module_name=module_dir.name,
            version=version,
            command=triggered_by,
            summary=(
                f"Dynamic context handoff: usage reached {usage_pct * 100:.1f}% "
                f"of the context window (threshold {threshold_pct * 100:.0f}%) while "
                f"running `{triggered_by}`. {tasks_done}/{tasks_total} tasks done. "
                "A fresh session should resume from this file without re-deriving "
                "already-completed work."
            ),
            models=[],
            tasks_done=tasks_done,
            tasks_total=tasks_total,
            extra={
                "context_handoff": {
                    "usage_pct": round(usage_pct * 100, 1),
                    "threshold_pct": round(threshold_pct * 100, 1),
                    "triggered_by": triggered_by,
                    "triggered_at": now_iso,
                }
            },
        )
        return True
    except Exception as exc:  # noqa: BLE001 - never let the guard crash a real turn
        logger.warning("[odoo-agent-pro-kit] context handoff write failed: %s", exc)
        return False
    finally:
        sys.path.remove(str(_CONTEXT_WRITER.parent)) if str(_CONTEXT_WRITER.parent) in sys.path else None


def inject_into_chat(ctx: Any, message: str, role: str = "user") -> bool:
    """Queue ``message`` as a turn in the chat this hook or command serves.

    A hosted chat (Murmur, the desktop app) is reached through Hermes's gateway, which needs the
    chat's session key; Hermes binds it while a command or hook runs. The CLI ignores it."""
    session_key = ""
    try:
        from gateway.session_context import get_session_env

        session_key = get_session_env("HERMES_SESSION_KEY")
    except Exception:  # noqa: BLE001 - an older Hermes has no session context
        pass
    if not session_key:
        return bool(ctx.inject_message(message, role=role))
    return bool(ctx.inject_message(message, role=role, session_key=session_key))


def maybe_handle_context_pressure(ctx: Any, **hook_kwargs: Any) -> None:
    """post_api_request handler: check usage, write handoff, nudge the agent.

    Best-effort throughout — any failure is logged and swallowed so this
    guard can never break a real turn (matches the plugin's existing
    _close_all_connections / _on_session_start fail-open convention).
    """
    try:
        usage = hook_kwargs.get("usage")
        base_threshold = float(
            ctx.get_config("context_handoff.threshold_pct", _DEFAULT_THRESHOLD_PCT)
        )
        context_window_tokens = int(
            ctx.get_config("context_handoff.context_window_tokens", _DEFAULT_CONTEXT_WINDOW_TOKENS)
        )
        retrigger_bucket = float(
            ctx.get_config("context_handoff.retrigger_bucket_pct", _RETRIGGER_BUCKET_PCT)
        )

        # Hermes sends the model's real window; the config value is only the fallback.
        given_window = hook_kwargs.get("context_length")
        if isinstance(given_window, (int, float)) and given_window > 0:
            context_window_tokens = int(given_window)
        tokens = context_tokens(usage)
        usage_pct = tokens / context_window_tokens if tokens else _usage_pct(usage, context_window_tokens)
        if usage_pct is None:
            return

        module_dir = _find_module_dir()
        if module_dir is None:
            return  # not inside an active /plan-analysis workspace; nothing to hand off

        tasks_md = module_dir / "docs" / "tasks.md"
        _tasks_done, tasks_total = _count_tasks(tasks_md) if tasks_md.is_file() else (0, 0)
        threshold_pct = _effective_threshold_pct(base_threshold, tasks_total)

        if usage_pct < threshold_pct:
            return

        key = str(module_dir)
        bucket = (usage_pct // retrigger_bucket) * retrigger_bucket
        if _last_triggered_bucket.get(key) == bucket:
            return  # already handed off at this usage level for this module

        triggered_by = hook_kwargs.get("model") or "unknown-command"
        written = _write_handoff(module_dir, usage_pct, threshold_pct, str(triggered_by))
        if not written:
            return
        _last_triggered_bucket[key] = bucket

        message = (
            f"[odoo-agent-pro-kit] Context usage reached {usage_pct * 100:.1f}% "
            f"(threshold {threshold_pct * 100:.0f}% for this module's "
            f"{tasks_total}-task size). Episodic context has been written to "
            f"{module_dir}/CLAUDE.md (+GEMINI.md/AGENTS.md) per "
            "CommandingSystem/context_handoff_workflow.md. Finish the current "
            "step cleanly, do not start new large work, and tell the user this "
            "session should be reset — the next session will resume from "
            "CLAUDE.md + docs/tasks.md automatically."
        )
        logger.warning(message)
        try:
            inject_into_chat(ctx, message, role="system")
        except Exception as exc:  # noqa: BLE001
            logger.debug("[odoo-agent-pro-kit] inject_message unavailable: %s", exc)
    except Exception as exc:  # noqa: BLE001 - fail-open guard
        logger.warning("[odoo-agent-pro-kit] context pressure guard failed: %s", exc)


# ---------------------------------------------------------------------------
# Hosted mode (Hermes behind a gateway, the module in another container).
#
# Hermes compacts a chat by itself, inside the running turn, once the context passes its
# compression.threshold. This guard puts two notes in front of the agent: a save note just
# before that compaction and a resume note just after it. transform_tool_result is the only
# hook that reaches the model inside a running turn; pre_llm_call covers the start of a turn.
# The deployed Hermes has no post_compaction hook, so a compaction shows as the prompt
# shrinking by a third. The agent writes the files itself: they are not on this filesystem.
# ---------------------------------------------------------------------------

_DEFAULT_COMPACTION_THRESHOLD_PCT = 0.60
_SAVE_MARGIN = 0.05
_SHRINK_RATIO = 2 / 3
_LARGE_WINDOW = 512_000  # Hermes floors smaller windows at 0.75 (raise-only)

# session_id -> {"command": dict | None, "tokens": int, "saved": bool, "note": str | None}
_hosted: dict[str, dict] = {}


def compaction_threshold(context_length: int, configured: float) -> float:
    """Hermes's effective compaction ratio for a window of ``context_length`` tokens."""
    if context_length >= _LARGE_WINDOW:
        return configured
    return max(0.75, configured)


def context_tokens(usage: Any) -> Optional[int]:
    """Tokens the last request sent: the size of the chat's context."""
    if not isinstance(usage, dict):
        return None
    prompt = usage.get("prompt_tokens")
    if isinstance(prompt, (int, float)) and prompt > 0:
        return int(prompt)
    given = usage.get("input_tokens")
    if isinstance(given, (int, float)) and given > 0:
        cached = usage.get("cache_read_tokens")
        return int(given) + (int(cached) if isinstance(cached, (int, float)) and cached > 0 else 0)
    return None


def _command_text(command: Optional[dict]) -> Optional[str]:
    if not command:
        return None
    return " ".join(p for p in (f"/{command['name']}", command.get("version"), command.get("args")) if p)


def _save_note(command: Optional[dict], pct: float, limit: float) -> str:
    what = f" for {_command_text(command)}" if command else ""
    return (
        f"[odoo-agent-pro-kit] This chat is at {pct * 100:.0f}% of its context; Hermes compacts it at "
        f"{limit * 100:.0f}%. Before your next step{what}: update sessions/<module>_progress.json and "
        "docs/tasks.md, and write the handoff to CLAUDE.md and AGENTS.md in the module folder "
        "(CommandingSystem/context_handoff_workflow.md). Then carry on with the same task; do not stop "
        "or ask the user to reset."
    )


def _resume_note(command: Optional[dict]) -> str:
    what = _command_text(command) or "the kit command you were running"
    return (
        f"[odoo-agent-pro-kit] This chat was just compacted. To carry on {what}: re-read CLAUDE.md, "
        "docs/tasks.md and sessions/<module>_progress.json in the module folder, then continue from "
        "the first open task with the same rules."
    )


def _state(session_id: Any) -> Optional[dict]:
    if not isinstance(session_id, str) or not session_id:
        return None
    return _hosted.setdefault(session_id, {"command": None, "tokens": 0, "saved": False, "note": None})


def on_post_api_request(ctx: Any, **kw: Any) -> None:
    try:
        state = _state(kw.get("session_id"))
        tokens = context_tokens(kw.get("usage"))
        window = kw.get("context_length")
        if state is None or tokens is None or not isinstance(window, (int, float)) or window <= 0:
            return
        configured = float(
            ctx.get_config("context_handoff.compaction_threshold_pct", _DEFAULT_COMPACTION_THRESHOLD_PCT)
        )
        limit = compaction_threshold(int(window), configured)
        previous, state["tokens"] = state["tokens"], tokens
        if previous and tokens <= previous * _SHRINK_RATIO and (state["saved"] or previous >= window * limit / 2):
            state["saved"] = False
            state["note"] = _resume_note(state["command"])
            return
        pct = tokens / window
        if not state["saved"] and pct >= limit - _SAVE_MARGIN:
            state["saved"] = True
            state["note"] = _save_note(state["command"], pct, limit)
    except Exception as exc:  # noqa: BLE001 - fail-open guard
        logger.warning("[odoo-agent-pro-kit] hosted context guard failed: %s", exc)


def _take_note(session_id: Any) -> Optional[str]:
    state = _hosted.get(session_id) if isinstance(session_id, str) else None
    if not state or not state.get("note"):
        return None
    note, state["note"] = state["note"], None
    return note


def on_pre_llm_call(ctx: Any, **kw: Any) -> Optional[dict]:
    try:
        state = _state(kw.get("session_id"))
        if state is None:
            return None
        command = parse_command_marker(kw.get("user_message"))
        if command:
            state["command"] = command
        note = _take_note(kw.get("session_id"))
        return {"context": note} if note else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[odoo-agent-pro-kit] hosted context guard failed: %s", exc)
        return None


def on_transform_tool_result(ctx: Any, **kw: Any) -> Optional[str]:
    try:
        result = kw.get("result")
        if not isinstance(result, str):
            return None
        note = _take_note(kw.get("session_id"))
        return f"{result}\n\n{note}" if note else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[odoo-agent-pro-kit] hosted context guard failed: %s", exc)
        return None
