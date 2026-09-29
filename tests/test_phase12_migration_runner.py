"""Phase 12 (findings 2, 3, 4): the generic batch migration runner, with fake sandboxctl and agent binaries.

The runner calls the real test-parity.py and the real hook gates; only the Odoo runtime and the
LLM agent are faked.
"""
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "sandbox/scripts/migration-runner.sh"

# Fake sandboxctl: `create` prints the session; `module S install M` fails for $FAKE_INSTALL_FAIL;
# `module S test M` appends one passing test per module to the session's odoo.log.
FAKE_SANDBOXCTL = r'''#!/bin/bash
echo "sandboxctl $*" >> "$FAKE_CALLS"
case "$1" in
  create)
    session=""; while [ $# -gt 0 ]; do [ "$1" = --session ] && session=$2; shift; done
    mkdir -p "$SANDBOX_SESSIONS_DIR/$session/logs"; : > "$SANDBOX_SESSIONS_DIR/$session/logs/odoo.log"
    echo "$session";;
  module)
    session=$2 action=$3 module=$4
    if [ "$action" = install ] && [[ " ${FAKE_INSTALL_FAIL:-} " == *" $module "* ]]; then exit 1; fi
    if [ "$action" = test ] && [[ " ${FAKE_NO_TESTS:-} " != *" $module "* ]]; then
      echo "2026-09-29 10:00:00,000 1 INFO sandbox_db odoo.addons.$module.tests.test_x: Starting T.test_ok ..." >> "$SANDBOX_SESSIONS_DIR/$session/logs/odoo.log"
    fi;;
  destroy) ;;
esac
exit 0
'''

# Fake agent: records the prompt; its behaviour per stage comes from FAKE_AGENT_<STAGE> (a shell snippet).
FAKE_AGENT = r'''#!/bin/bash
prompt="${@: -1}"
echo "AGENT[$RUNNER_STAGE] $prompt" | head -c 2000 >> "$FAKE_CALLS"; echo >> "$FAKE_CALLS"
var="FAKE_AGENT_$(echo "$RUNNER_STAGE" | tr a-z A-Z)"
[ -n "${!var:-}" ] && eval "${!var}"
exit 0
'''


def executable(path, text):
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def module(source, name):
    (source / name).mkdir(parents=True)
    (source / name / "__manifest__.py").write_text(f"{{'name': '{name}', 'version': '19.0.1.0.0', 'depends': ['base']}}")


@pytest.fixture
def env(tmp_path):
    calls = tmp_path / "calls.txt"
    calls.write_text("")
    environment = {**os.environ,
                   "SANDBOXCTL": str(executable(tmp_path / "sandboxctl", FAKE_SANDBOXCTL)),
                   "AGENT_CMD": str(executable(tmp_path / "agent", FAKE_AGENT)),
                   "SANDBOX_SESSIONS_DIR": str(tmp_path / "sessions"), "FAKE_CALLS": str(calls),
                   "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@localhost", "GIT_COMMITTER_NAME": "t",
                   "GIT_COMMITTER_EMAIL": "t@localhost"}
    return environment


def groups_file(tmp_path, *groups):
    lines = []
    for name, modules in groups:
        source = tmp_path / f"src-{name}"
        for mod in modules:
            module(source, mod)
        lines.append(f"{name} {source} {','.join(modules)}")
    path = tmp_path / "groups.txt"
    path.write_text("# name source modules [requirements] [baseline-freeze]\n" + "\n".join(lines) + "\n")
    return path


def run(tmp_path, env, groups, *extra, **more_env):
    return subprocess.run(["bash", str(RUNNER), "--groups", str(groups), "--from", "19", "--to", "20",
                           "--out", str(tmp_path / "out"), *extra],
                          capture_output=True, text=True, env={**env, **more_env}, timeout=120)


def status(tmp_path, group):
    path = tmp_path / "out" / group / "status.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def stage_status(tmp_path, group, stage):
    return [s for s in status(tmp_path, group) if s.get("stage") == stage and "status" in s]


def calls(tmp_path):
    return (tmp_path / "calls.txt").read_text()


def test_runner_is_generic():
    text = RUNNER.read_text()
    assert "vpcs" not in text.lower() and "/Users/" not in text and "/home/" not in text
    assert "VPCS-Cloud" not in text


def test_baseline_and_verify_record_install_codes_and_pass(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    result = run(tmp_path, env, groups, "--stages", "baseline verify")
    assert result.returncode == 0, result.stdout + result.stderr
    assert stage_status(tmp_path, "c", "baseline")[-1]["status"] == "done"
    installs = [s for s in status(tmp_path, "c") if s.get("event") == "install"]
    assert [(s["stage"], s["module"], s["rc"]) for s in installs] == [("baseline", "mod_one", 0), ("verify", "mod_one", 0)]
    verify = stage_status(tmp_path, "c", "verify")[-1]
    assert verify["status"] == "done" and verify["pass"] is True
    report = json.loads((tmp_path / "out/c/parity.json").read_text())
    assert report["pass"] is True and report["modules"][0]["install_exit"] == 0
    assert "sandboxctl create --version 19 --module mod_one" in calls(tmp_path)
    assert "sandboxctl create --version 20 --module mod_one" in calls(tmp_path)


def test_a_broken_install_fails_verify_even_with_parity(tmp_path, env):
    groups = groups_file(tmp_path, ("a", ["mod_one", "mod_two"]))
    run(tmp_path, env, groups, "--stages", "baseline", FAKE_NO_TESTS="mod_two")
    result = run(tmp_path, env, groups, "--stages", "verify", FAKE_INSTALL_FAIL="mod_two", FAKE_NO_TESTS="mod_two")
    assert result.returncode == 1
    verify = stage_status(tmp_path, "a", "verify")[-1]
    assert verify["status"] == "failed" and verify["pass"] is False and verify["parity"] is True
    report = json.loads((tmp_path / "out/a/parity.json").read_text())
    assert {m["module"]: m["install_exit"] for m in report["modules"]} == {"mod_one": 0, "mod_two": 1}


def test_agent_prompts_are_plain_words_naming_the_workflow_file(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    run(tmp_path, env, groups, "--stages", "plan")
    prompts = [line for line in calls(tmp_path).splitlines() if line.startswith("AGENT[plan]")]
    assert prompts
    prompt = prompts[0].removeprefix("AGENT[plan] ")
    assert not prompt.lstrip().startswith("/") and "plan_analysis_workflow.md" in prompt


def test_code_stage_is_refused_by_the_gate_without_a_plan(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    result = run(tmp_path, env, groups, "--stages", "code")
    assert result.returncode == 1
    code = stage_status(tmp_path, "c", "code")[-1]
    assert code["status"] == "blocked" and code["rc"] == 2
    assert "AGENT[code]" not in calls(tmp_path)


def test_code_stage_runs_after_a_plan_and_names_start_coding_workflow(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    plan = 'mkdir -p docs && printf -- "- [ ] Task 1: migrate\\n" > docs/tasks.md && git add -A && git commit -qm plan'
    code = ('printf -- "- [x] Task 1: migrate\\n" > docs/tasks.md && mkdir -p sessions && '
            'echo \'{"backend_tests_passed": true}\' > sessions/$(basename $PWD)_progress.json && git add -A && git commit -qm code')
    result = run(tmp_path, env, groups, "--stages", "plan code", FAKE_AGENT_PLAN=plan, FAKE_AGENT_CODE=code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert stage_status(tmp_path, "c", "code")[-1]["status"] == "done"
    assert "start_coding_workflow.md" in calls(tmp_path)


def test_groups_run_serially_by_default(tmp_path, env):
    groups = groups_file(tmp_path, ("a", ["mod_a"]), ("b", ["mod_b"]))
    result = run(tmp_path, env, groups, "--stages", "baseline verify")
    assert result.returncode == 0, result.stderr
    text = calls(tmp_path)
    assert text.index("--version 20 --module mod_a") < text.index("--version 19 --module mod_b")


def test_parallel_only_when_asked(tmp_path, env):
    groups = groups_file(tmp_path, ("a", ["mod_a"]), ("b", ["mod_b"]))
    result = run(tmp_path, env, groups, "--stages", "baseline", "--parallel")
    assert result.returncode == 0, result.stderr
    assert stage_status(tmp_path, "a", "baseline")[-1]["status"] == "done"
    assert stage_status(tmp_path, "b", "baseline")[-1]["status"] == "done"


def test_resume_skips_finished_stages(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    run(tmp_path, env, groups, "--stages", "baseline")
    (tmp_path / "calls.txt").write_text("")
    result = run(tmp_path, env, groups, "--stages", "baseline verify")
    assert result.returncode == 0, result.stderr
    assert "--version 19" not in calls(tmp_path) and "--version 20" in calls(tmp_path)
    assert any(s["stage"] == "baseline" and s["status"] == "skipped" for s in stage_status(tmp_path, "c", "baseline"))


def test_quota_exhaustion_stops_the_batch(tmp_path, env):
    groups = groups_file(tmp_path, ("a", ["mod_a"]), ("b", ["mod_b"]))
    result = run(tmp_path, env, groups, "--stages", "plan",
                 FAKE_AGENT_PLAN="echo \"You've hit your usage limit. Try again at 12:46 PM.\"")
    assert result.returncode == 1
    assert stage_status(tmp_path, "a", "plan")[-1]["status"] == "quota_stop"
    assert "AGENT[plan]" in calls(tmp_path) and calls(tmp_path).count("AGENT[plan]") == 1
    assert stage_status(tmp_path, "b", "plan")[-1]["status"] == "not_started"


def test_group_budget_stops_the_group_before_the_next_agent_stage(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    result = run(tmp_path, env, groups, "--stages", "plan code", "--group-budget-seconds", "0")
    assert result.returncode == 1
    assert stage_status(tmp_path, "c", "plan")[-1]["status"] == "budget_stop"
    assert "AGENT[" not in calls(tmp_path)


def test_every_status_line_is_json_with_a_timestamp(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    run(tmp_path, env, groups, "--stages", "baseline")
    lines = status(tmp_path, "c")
    assert lines and all("ts" in line and line["group"] == "c" for line in lines)


def test_usage_errors_exit_2(env):
    result = subprocess.run(["bash", str(RUNNER), "--from", "19"], capture_output=True, text=True, env=env)
    assert result.returncode == 2


def test_rerun_repeats_a_finished_stage_on_purpose(tmp_path, env):
    groups = groups_file(tmp_path, ("c", ["mod_one"]))
    run(tmp_path, env, groups, "--stages", "baseline verify")
    (tmp_path / "calls.txt").write_text("")
    result = run(tmp_path, env, groups, "--stages", "baseline verify", "--rerun", "verify")
    assert result.returncode == 0, result.stderr
    assert "--version 19" not in calls(tmp_path) and "--version 20" in calls(tmp_path)
    assert [s["status"] for s in stage_status(tmp_path, "c", "verify")] == ["done", "done"]
