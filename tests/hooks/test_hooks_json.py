from __future__ import annotations
import json
from pathlib import Path

_HJ = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "hooks.json"


def test_valid_json_and_events():
    data = json.loads(_HJ.read_text())
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse",
                  "PostToolUse", "Stop", "SessionEnd", "PreCompact"):
        assert event in data, f"missing {event}"


def test_odoo_hook_referenced_per_event():
    data = json.loads(_HJ.read_text())
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"):
        blob = json.dumps(data[event])
        assert "odoo_hook.py" in blob and event.split()[0] in blob


def test_precompact_still_save_progress():
    data = json.loads(_HJ.read_text())
    assert "save_progress.sh" in json.dumps(data["PreCompact"])


def test_stop_no_longer_runs_cleanup_mcp():
    data = json.loads(_HJ.read_text())
    assert "cleanup_mcp.sh" not in json.dumps(data["Stop"])
