from __future__ import annotations
import json
from pathlib import Path

_HJ = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "hooks.json"


def _hooks() -> dict:
    """Claude Code plugin hooks.json wraps the event map under a ``hooks`` key
    (same shape as the ``hooks`` block of settings.json). ``claude plugin
    validate`` rejects a bare top-level event map."""
    data = json.loads(_HJ.read_text())
    assert "hooks" in data, "hooks.json must have a top-level `hooks` key"
    return data["hooks"]


def test_valid_json_and_events():
    events = _hooks()
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse",
                  "PostToolUse", "Stop", "SessionEnd", "PreCompact"):
        assert event in events, f"missing {event}"


def test_odoo_hook_referenced_per_event():
    events = _hooks()
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        blob = json.dumps(events[event])
        assert "odoo_hook.py" in blob and event.split()[0] in blob


def test_precompact_still_save_progress():
    assert "save_progress.sh" in json.dumps(_hooks()["PreCompact"])


def test_stop_no_longer_runs_cleanup_mcp():
    assert "cleanup_mcp.sh" not in json.dumps(_hooks()["Stop"])
