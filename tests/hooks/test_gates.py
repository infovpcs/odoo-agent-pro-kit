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
