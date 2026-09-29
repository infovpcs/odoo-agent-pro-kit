"""Phase 12 (finding 3): parity alone is not the pass criterion; installs and test presence count too."""
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sandbox/scripts/test-parity.py"


def load():
    loader = importlib.machinery.SourceFileLoader("test_parity_p12", str(SCRIPT))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def line(level, addon, message):
    return f"2026-09-28 08:04:45,515 1 {level} sandbox_db odoo.addons.{addon}.tests.test_x: {message}"


def write(path, *lines):
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def test_all_modules_installed_and_tested_passes():
    parity = load()
    baseline = {"a/t:T.x": "passed", "b/t:T.y": "failed"}
    target = {"a/t:T.x": "passed", "b/t:T.y": "failed"}
    check = parity.module_check(baseline, target, ["a", "b"], {"a": 0, "b": 0})
    assert check["ok"] is True and [m["ok"] for m in check["modules"]] == [True, True]


def test_a_failed_install_fails_even_when_no_baseline_pass_regresses():
    parity = load()
    # Group A 2026-09-28: the module had only errors on 19, so parity alone said PASS.
    baseline = {"a/t:T.x": "passed", "blog/t:T.e": "error"}
    target = {"a/t:T.x": "passed"}
    assert parity.compare(baseline, target)["parity"] is True
    check = parity.module_check(baseline, target, ["a", "blog"], {"a": 0, "blog": 1})
    assert check["ok"] is False
    blog = next(m for m in check["modules"] if m["module"] == "blog")
    assert blog["ok"] is False and "install" in blog["reason"]


def test_a_module_with_baseline_tests_but_none_on_target_fails():
    parity = load()
    baseline = {"a/t:T.x": "error"}
    check = parity.module_check(baseline, {}, ["a"], {"a": 0})
    assert check["ok"] is False and "no test result" in check["modules"][0]["reason"]


def test_a_module_without_tests_on_either_side_passes_when_installed():
    parity = load()
    check = parity.module_check({}, {}, ["livechat"], {"livechat": 0})
    assert check["ok"] is True


def test_an_expected_module_without_a_recorded_install_fails():
    parity = load()
    check = parity.module_check({"a/t:T.x": "passed"}, {"a/t:T.x": "passed"}, ["a", "b"], {"a": 0})
    assert check["ok"] is False
    assert next(m for m in check["modules"] if m["module"] == "b")["reason"] == "install exit code not recorded"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_cli_fails_a_broken_install_and_writes_the_module_table(tmp_path):
    base = write(tmp_path / "b.log", line("INFO", "a", "Starting T.x ..."), line("INFO", "blog", "Starting T.e ..."),
                 line("ERROR", "blog", "ERROR: T.e"))
    target = write(tmp_path / "t.log", line("INFO", "a", "Starting T.x ..."))
    out = tmp_path / "p.json"
    result = run(base, target, "--expect-module", "a", "--expect-module", "blog",
                 "--install-exit", "a=0", "--install-exit", "blog=1", "--json", str(out))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "parity: PASS" in result.stdout and "result: FAIL" in result.stdout
    report = json.loads(out.read_text())
    assert report["pass"] is False and report["parity"] is True
    assert {m["module"]: m["install_exit"] for m in report["modules"]} == {"a": 0, "blog": 1}


def test_cli_passes_when_every_expected_module_installs(tmp_path):
    base = write(tmp_path / "b.log", line("INFO", "a", "Starting T.x ..."))
    target = write(tmp_path / "t.log", line("INFO", "a", "Starting T.x ..."))
    result = run(base, target, "--expect-module", "a", "--install-exit", "a=0")
    assert result.returncode == 0 and "result: PASS" in result.stdout


def test_cli_rejects_a_malformed_install_exit(tmp_path):
    base = write(tmp_path / "b.log", line("INFO", "a", "Starting T.x ..."))
    result = run(base, base, "--expect-module", "a", "--install-exit", "a:zero")
    assert result.returncode == 2 and "--install-exit expects MODULE=CODE" in result.stderr


def test_without_expected_modules_parity_decides_alone(tmp_path):
    base = write(tmp_path / "b.log", line("INFO", "a", "Starting T.x ..."))
    out = tmp_path / "p.json"
    result = run(base, base, "--json", str(out))
    report = json.loads(out.read_text())
    assert result.returncode == 0 and report["pass"] is True and report["modules"] == []
