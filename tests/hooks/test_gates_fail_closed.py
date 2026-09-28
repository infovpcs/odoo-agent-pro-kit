# tests/hooks/test_gates_fail_closed.py
"""Phase 11 run 1: the command gates passed without checking anything when the target had no
root docs/tasks.md (a multi-module repository before planning, or a checklist kept inside the
single module). A recognisable Odoo target must be gated; only non-Odoo directories stay out of
scope."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_MOD_PATH = Path(__file__).resolve().parents[2] / "plugin" / "hooks" / "odoo_hook.py"
_spec = importlib.util.spec_from_file_location("odoo_hook_fail_closed", _MOD_PATH)
odoo_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(odoo_hook)


def _run(event, payload):
    return odoo_hook.main([event], json.dumps(payload))


def _repo(tmp_path, *modules):
    root = tmp_path / "group-x"
    (root / ".git").mkdir(parents=True)
    for name in modules:
        (root / name).mkdir()
        (root / name / "__manifest__.py").write_text("{'name': '%s', 'depends': ['base']}" % name)
    return root


def _tasks(directory, text):
    (directory / "docs").mkdir(parents=True, exist_ok=True)
    (directory / "docs" / "tasks.md").write_text(text)


def _progress(directory, data):
    (directory / "sessions").mkdir(exist_ok=True)
    (directory / "sessions" / f"{directory.name}_progress.json").write_text(json.dumps(data))


PARITY = {"backend_tests_passed": False, "backend_tests_baseline_parity": True,
          "backend_tests_baseline": "parity.json PASS"}


def test_start_coding_blocks_in_a_module_repository_without_a_plan(tmp_path, capsys):
    root = _repo(tmp_path, "mod_a", "mod_b")
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/start-coding 20"}) == 2
    assert "docs/tasks.md" in capsys.readouterr().err


def test_testing_blocks_in_a_module_repository_without_a_plan(tmp_path):
    root = _repo(tmp_path, "mod_a", "mod_b")
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 2


def test_start_coding_blocks_inside_a_module_without_a_plan(tmp_path):
    root = _repo(tmp_path, "mod_a")
    assert _run("UserPromptSubmit", {"cwd": str(root / "mod_a"), "prompt": "/start-coding 20"}) == 2


def test_checklist_inside_the_only_module_is_the_one_gated(tmp_path, capsys):
    root = _repo(tmp_path, "mod_a")
    _tasks(root / "mod_a", "- [x] Task 1\n- [ ] Task 2\n")
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 2
    assert "incomplete tasks" in capsys.readouterr().err


def test_outcome_recorded_next_to_a_different_checklist_does_not_count(tmp_path):
    # Group C: checklist in mod_a/docs/, outcome in the repository's sessions/.
    root = _repo(tmp_path, "mod_a")
    _tasks(root / "mod_a", "- [x] Task 1\n")
    _progress(root, PARITY)
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 2


def test_testing_passes_when_the_module_checklist_and_outcome_agree(tmp_path):
    root = _repo(tmp_path, "mod_a")
    _tasks(root / "mod_a", "- [x] Task 1\n")
    _progress(root / "mod_a", PARITY)
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 0


def test_root_checklist_still_wins_in_a_multi_module_repository(tmp_path):
    root = _repo(tmp_path, "mod_a", "mod_b")
    _tasks(root, "- [x] Task 1\n")
    _progress(root, PARITY)
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 0


def test_several_module_checklists_without_a_root_one_block(tmp_path, capsys):
    root = _repo(tmp_path, "mod_a", "mod_b")
    _tasks(root / "mod_a", "- [x] Task 1\n")
    _tasks(root / "mod_b", "- [x] Task 1\n")
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 2
    assert "docs/tasks.md" in capsys.readouterr().err


def test_stop_enforces_the_outcome_record_for_a_checklist_inside_the_module(tmp_path):
    root = _repo(tmp_path, "mod_a")
    _tasks(root / "mod_a", "- [x] Task 1\n")
    assert _run("Stop", {"cwd": str(root)}) == 2
    _progress(root / "mod_a", PARITY)
    assert _run("Stop", {"cwd": str(root)}) == 0


def test_a_plain_git_repository_stays_out_of_scope(tmp_path):
    root = tmp_path / "notodoo"
    (root / ".git").mkdir(parents=True)
    (root / "src").mkdir()
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/testing 20"}) == 0
    assert _run("Stop", {"cwd": str(root)}) == 0


def test_modules_above_the_repository_root_are_not_scanned(tmp_path):
    (tmp_path / "stray_mod").mkdir()
    (tmp_path / "stray_mod" / "__manifest__.py").write_text("{}")
    root = tmp_path / "project"
    (root / ".git").mkdir(parents=True)
    assert _run("UserPromptSubmit", {"cwd": str(root), "prompt": "/start-coding 20"}) == 0
