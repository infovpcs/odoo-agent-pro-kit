# Phase 12 (finding 9): a migration's /testing must record the live UI check outcome.
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugin" / "hooks"))
from checks import gates  # noqa: E402

_spec = importlib.util.spec_from_file_location("odoo_hook_p12", ROOT / "plugin" / "hooks" / "odoo_hook.py")
odoo_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(odoo_hook)

MIGRATION = {"backend_tests_passed": False, "backend_tests_baseline_parity": True,
             "backend_tests_baseline": "19.0: mymod 2 failed of 8"}


def _module(tmp_path, progress):
    (tmp_path / ".git").mkdir(parents=True, exist_ok=True)
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [x] t1\n- [x] t2\n")
    (mod / "sessions").mkdir()
    (mod / "sessions" / "mymod_progress.json").write_text(json.dumps(progress))
    return mod


def _transcript(tmp_path, prompt):
    path = tmp_path / "transcript.jsonl"
    path.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}}) + "\n")
    return str(path)


def _stop(mod, **payload):
    return odoo_hook.main(["Stop"], json.dumps({"cwd": str(mod), **payload}))


def test_migration_target_without_ui_check_needs_one(tmp_path):
    assert gates.needs_ui_check_record(_module(tmp_path, MIGRATION)) is True


def test_recorded_ui_check_satisfies_the_gate_even_when_failed(tmp_path):
    result = tmp_path / "ui.json"
    result.write_text("{}")
    mod = _module(tmp_path, {**MIGRATION, "ui_check": {"passed": False, "result": str(result)}})
    assert gates.needs_ui_check_record(mod) is False


def test_ui_check_record_must_point_at_an_existing_result(tmp_path):
    mod = _module(tmp_path, {**MIGRATION, "ui_check": {"passed": True, "result": str(tmp_path / "missing.json")}})
    assert gates.needs_ui_check_record(mod) is True
    mod2 = _module(tmp_path / "b", {**MIGRATION, "ui_check": True})
    assert gates.needs_ui_check_record(mod2) is True


def test_ui_check_result_may_be_relative_to_the_module(tmp_path):
    mod = _module(tmp_path, {**MIGRATION, "ui_check": {"passed": True, "result": "docs/ui-check.json"}})
    (mod / "docs" / "ui-check.json").write_text("{}")
    assert gates.needs_ui_check_record(mod) is False


def test_new_module_is_not_a_migration_target(tmp_path):
    assert gates.needs_ui_check_record(_module(tmp_path, {"backend_tests_passed": True})) is False
    assert gates.needs_ui_check_record(None) is False


def test_stop_in_a_testing_session_blocks_and_names_the_ui_check(tmp_path, capsys):
    mod = _module(tmp_path, MIGRATION)
    assert _stop(mod, transcript_path=_transcript(tmp_path, "/testing 20 mymod")) == 2
    err = capsys.readouterr().err
    assert "sandbox/scripts/ui-check.py" in err and '"ui_check"' in err and "sessions/mymod_progress.json" in err
    assert _stop(mod, transcript_path=_transcript(tmp_path, "/testing 20 mymod"), stop_hook_active=True) == 0


def test_stop_recognises_a_plain_words_testing_prompt(tmp_path):
    # Runner prompts name the workflow file instead of a leading slash command (finding 2).
    mod = _module(tmp_path, MIGRATION)
    prompt = "Follow plugin/skills/CommandingSystem/testing_workflow.md for Odoo 20 module mymod."
    assert _stop(mod, prompt=prompt) == 2


def test_stop_outside_a_testing_session_does_not_ask_for_the_ui_check(tmp_path):
    mod = _module(tmp_path, MIGRATION)
    assert _stop(mod, transcript_path=_transcript(tmp_path, "/start-coding 20 mymod")) == 0
    assert _stop(mod) == 0
