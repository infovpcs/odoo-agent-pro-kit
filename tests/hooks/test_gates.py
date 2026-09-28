from __future__ import annotations
import json
from plugin.hooks.checks import gates


def _mk(tmp_path, tasks="- [x] a\n- [x] b\n", passed=True):
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text(tasks)
    (mod / "sessions").mkdir()
    (mod / "sessions" / "mymod_progress.json").write_text(json.dumps({"backend_tests_passed": passed}))
    return mod


def test_start_coding_ok(tmp_path):
    mod = _mk(tmp_path)
    assert gates.check_start_coding(mod).ok is True


def test_start_coding_missing_tasks(tmp_path):
    mod = tmp_path / "empty"
    mod.mkdir()
    g = gates.check_start_coding(mod)
    assert g.ok is False and "plan-analysis" in g.message


def test_testing_ok(tmp_path):
    mod = _mk(tmp_path)
    assert gates.check_testing(mod).ok is True


def test_testing_incomplete_tasks(tmp_path):
    mod = _mk(tmp_path, tasks="- [x] a\n- [ ] b\n")
    g = gates.check_testing(mod)
    assert g.ok is False and "start-coding" in g.message


def test_testing_backend_not_passed(tmp_path):
    mod = _mk(tmp_path, passed=False)
    g = gates.check_testing(mod)
    assert g.ok is False and "backend" in g.message.lower()


def test_none_module_dir_ok(tmp_path):
    assert gates.check_start_coding(None).ok is True
    assert gates.check_testing(None).ok is True


def test_testing_malformed_progress_json(tmp_path):
    """Hardening: non-dict JSON values should not crash on .get()."""
    mod = tmp_path / "mymod"
    (mod / "docs").mkdir(parents=True)
    (mod / "docs" / "tasks.md").write_text("- [x] a\n- [x] b\n")
    (mod / "sessions").mkdir()
    # Write malformed JSON: a string literal instead of dict
    (mod / "sessions" / "mymod_progress.json").write_text('"null"')
    g = gates.check_testing(mod)
    assert g.ok is False and "backend" in g.message.lower()


def _progress(mod, data):
    (mod / "sessions" / "mymod_progress.json").write_text(json.dumps(data))


def test_testing_ok_on_recorded_baseline_parity(tmp_path):
    """Migrations keep pre-existing failures: parity with a recorded baseline passes the gate."""
    mod = _mk(tmp_path)
    _progress(mod, {"backend_tests_passed": False, "backend_tests_baseline_parity": True,
                    "backend_tests_baseline": "19.0: mymod 2 failed + 2 errors of 8"})
    assert gates.check_testing(mod).ok is True


def test_testing_parity_without_baseline_blocked(tmp_path):
    mod = _mk(tmp_path)
    _progress(mod, {"backend_tests_baseline_parity": True})
    g = gates.check_testing(mod)
    assert g.ok is False and "backend_tests_baseline" in g.message


def test_backend_record_needed_when_tasks_done_and_no_record(tmp_path):
    mod = _mk(tmp_path)
    (mod / "sessions" / "mymod_progress.json").unlink()
    assert gates.needs_backend_test_record(mod) is True
    _progress(mod, {"last_completed_task": "t"})
    assert gates.needs_backend_test_record(mod) is True


def test_backend_record_not_needed(tmp_path):
    assert gates.needs_backend_test_record(None) is False
    assert gates.needs_backend_test_record(_mk(tmp_path, passed=False)) is False  # honest failure recorded
    assert gates.needs_backend_test_record(_mk(tmp_path / "b", tasks="- [x] a\n- [ ] b\n")) is False
    assert gates.needs_backend_test_record(_mk(tmp_path / "c", tasks="# nothing yet\n")) is False


_PROSE_TASKS = "## 4. Migration Tasks\n\n**Task 1: Create Migration Stage**\n- Stage both modules\n"


def test_start_coding_blocks_tasks_without_checklist(tmp_path):
    """Phase 10: a prose tasks.md made every later task gate vacuous."""
    mod = _mk(tmp_path, tasks=_PROSE_TASKS)
    g = gates.check_start_coding(mod)
    assert g.ok is False and "- [ ]" in g.message and "plan-analysis" in g.message


def test_testing_blocks_tasks_without_checklist(tmp_path):
    mod = _mk(tmp_path, tasks=_PROSE_TASKS)
    g = gates.check_testing(mod)
    assert g.ok is False and "- [ ]" in g.message
