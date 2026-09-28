"""Phase 11: deterministic 19-vs-20 backend-test parity from two Odoo test logs (no LLM)."""
import importlib.machinery
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sandbox/scripts/test-parity.py"


def load():
    loader = importlib.machinery.SourceFileLoader("test_parity", str(SCRIPT))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def line(level, addon, test_file, message):
    return f"2026-09-28 08:04:45,515 1 {level} sandbox_db odoo.addons.{addon}.tests.{test_file}: {message} "


def log(*entries):
    return "\n".join(entries) + "\n"


BASELINE = log(
    line("INFO", "mod_a", "test_x", "Starting TestX.test_ok ..."),
    line("INFO", "mod_a", "test_x", "Starting TestX.test_fails ..."),
    line("ERROR", "mod_a", "test_x", "FAIL: TestX.test_fails"),
    "Traceback (most recent call last):",
    '  File "x.py", line 1, in test_fails',
    "AssertionError: 1 != 2",
    line("INFO", "mod_a", "test_x", "Starting TestX.test_errors ..."),
    line("ERROR", "mod_a", "test_x", "ERROR: TestX.test_errors"),
    line("INFO", "mod_b", "test_y", "Starting TestY.test_skip ..."),
    line("INFO", "mod_b", "test_y", "skipped TestY.test_skip : no network"),
    "2026-09-28 08:04:46,737 1 ERROR sandbox_db odoo.tests.result: 1 failed, 1 error(s) of 4 tests when loading database 'sandbox_db' ",
)


def test_parse_assigns_one_status_per_test():
    parity = load()
    assert parity.parse_log(BASELINE) == {
        "mod_a/test_x:TestX.test_ok": "passed",
        "mod_a/test_x:TestX.test_fails": "failed",
        "mod_a/test_x:TestX.test_errors": "error",
        "mod_b/test_y:TestY.test_skip": "skipped",
    }


def test_class_level_errors_are_recorded_as_errors():
    parity = load()
    text = log(line("ERROR", "mod_a", "test_x", "ERROR: setUpClass (odoo.addons.mod_a.tests.test_x.TestX)"))
    assert parity.parse_log(text) == {"mod_a/test_x:setUpClass (odoo.addons.mod_a.tests.test_x.TestX)": "error"}


def test_a_test_run_twice_keeps_its_worst_status():
    parity = load()
    text = log(line("INFO", "m", "t", "Starting T.test_a ..."),
               line("INFO", "m", "t", "Starting T.test_a ..."),
               line("ERROR", "m", "t", "FAIL: T.test_a"))
    assert parity.parse_log(text) == {"m/t:T.test_a": "failed"}


def test_same_results_are_parity():
    parity = load()
    report = parity.compare(parity.parse_log(BASELINE), parity.parse_log(BASELINE))
    assert report["parity"] is True and report["regressions"] == []
    assert report["summary"]["baseline"] == {"passed": 1, "failed": 1, "error": 1, "skipped": 1, "total": 4}


def test_a_baseline_pass_that_fails_errors_skips_or_vanishes_is_a_regression():
    parity = load()
    baseline = {"m/t:T.a": "passed", "m/t:T.b": "passed", "m/t:T.c": "passed", "m/t:T.d": "passed"}
    target = {"m/t:T.a": "failed", "m/t:T.b": "error", "m/t:T.c": "skipped"}
    report = parity.compare(baseline, target)
    assert report["parity"] is False
    assert [(r["test"], r["target"]) for r in report["regressions"]] == [
        ("m/t:T.a", "failed"), ("m/t:T.b", "error"), ("m/t:T.c", "skipped"), ("m/t:T.d", "missing")]


def test_baseline_failures_may_stay_failing_and_fixes_are_listed():
    parity = load()
    report = parity.compare({"m/t:T.a": "failed", "m/t:T.b": "error"}, {"m/t:T.a": "passed", "m/t:T.b": "error", "m/t:T.new": "passed"})
    assert report["parity"] is True
    assert [r["test"] for r in report["improvements"]] == ["m/t:T.a"]
    assert report["new"] == [{"test": "m/t:T.new", "target": "passed"}]


def test_module_filter_limits_the_comparison():
    parity = load()
    baseline = {"a/t:T.x": "passed", "b/t:T.y": "passed"}
    report = parity.compare(baseline, {"a/t:T.x": "passed"}, modules=["a"])
    assert report["parity"] is True and report["summary"]["baseline"]["total"] == 1


def run_cli(tmp_path, baseline, target, *extra):
    (tmp_path / "b.log").write_text(baseline)
    (tmp_path / "t.log").write_text(target)
    out = tmp_path / "parity.json"
    result = subprocess.run(["python3", str(SCRIPT), str(tmp_path / "b.log"), str(tmp_path / "t.log"), "--json", str(out), *extra],
                            capture_output=True, text=True)
    return result, (json.loads(out.read_text()) if out.exists() else None)


def test_cli_exit_zero_on_parity_and_writes_json(tmp_path):
    result, report = run_cli(tmp_path, BASELINE, BASELINE)
    assert result.returncode == 0, result.stderr
    assert report["parity"] is True and report["schema_version"] == "1.0.0"
    assert report["baseline_log"].endswith("b.log") and report["target_log"].endswith("t.log")


def test_cli_exit_one_on_regression(tmp_path):
    target = BASELINE.replace("Starting TestX.test_ok ...", "Starting TestX.test_ok ...\n" + line("ERROR", "mod_a", "test_x", "FAIL: TestX.test_ok"))
    result, report = run_cli(tmp_path, BASELINE, target)
    assert result.returncode == 1
    assert "mod_a/test_x:TestX.test_ok" in result.stdout
    assert report["parity"] is False


def test_cli_refuses_a_log_without_tests(tmp_path):
    result, _ = run_cli(tmp_path, BASELINE, "odoo started, no tests\n")
    assert result.returncode == 2 and "no tests" in result.stderr


def test_class_level_errors_from_the_suite_logger_are_attributed_to_their_addon():
    parity = load()
    text = log("2026-09-28 08:05:00,265 1 ERROR sandbox_db odoo.tests.suite: ERROR: setUpClass "
               "(odoo.addons.mod_a.tests.test_x_views.TestXViews)",
               "2026-09-28 08:05:00,300 1 ERROR sandbox_db odoo.tests.suite: ERROR: tearDownClass "
               "(odoo.addons.mod_b.tests.test_y.TestY)")
    assert parity.parse_log(text) == {
        "mod_a/test_x_views:setUpClass (odoo.addons.mod_a.tests.test_x_views.TestXViews)": "error",
        "mod_b/test_y:tearDownClass (odoo.addons.mod_b.tests.test_y.TestY)": "error",
    }
