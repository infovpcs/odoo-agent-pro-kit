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
            match = re.search(r"(?:odoo[_ ]?version|version)\s*[:=]\s*\"?(1[789])", meta.read_text(errors="replace"), re.IGNORECASE)
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

        usage_pct = _usage_pct(usage, context_window_tokens)
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
            ctx.inject_message(message, role="system")
        except Exception as exc:  # noqa: BLE001
            logger.debug("[odoo-agent-pro-kit] inject_message unavailable: %s", exc)
    except Exception as exc:  # noqa: BLE001 - fail-open guard
        logger.warning("[odoo-agent-pro-kit] context pressure guard failed: %s", exc)
