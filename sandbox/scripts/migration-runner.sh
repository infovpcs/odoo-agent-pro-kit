#!/usr/bin/env bash
# Batch Odoo version migration runner (Phase 12; from the Phase 11 batch run, findings 2, 3 and 4).
#
# Runs module groups through the stages  baseline -> plan -> code -> test -> verify:
#   baseline  (no LLM) install + test every module of the group on --from in a fresh session;
#             the full Odoo log is the reference for parity.
#   plan      (agent)  the kit's plan-analysis workflow writes docs/ in the group's work repository.
#   code      (agent)  the start-coding workflow; the kit's UserPromptSubmit gate runs first and the
#             Stop gate after (one re-prompt with the gate's own message if it blocks).
#   test      (agent)  the testing workflow, gated the same way (a migration must record its live UI
#             check, see sandbox/scripts/ui-check.py).
#   verify    (no LLM) the committed work (git archive HEAD) in a fresh --to session: install codes
#             per module, tests, then test-parity.py with the expected modules and install codes.
#
# Agent prompts are plain words that name the workflow file: a leading slash command made Codex
# end with "goal budget exhausted" and nothing written (finding 2). Codex does not run Claude Code
# hooks, so the runner calls the kit's hook entry point itself around the agent stages.
#
# Quota plan (finding 4): groups run one after another unless --parallel is given (parallel
# agents share one subscription quota); --group-budget-seconds stops a group before its next agent
# stage once its agents have used that much wall time; a usage-limit message from the agent stops
# the whole batch (quota_stop); a re-run resumes each group after its last finished stage.
#
# Every event appends one JSON line to OUT/<group>/status.jsonl:
#   {"ts": ..., "group": ..., "stage": ..., "status": "done|failed|blocked|skipped|budget_stop|quota_stop|not_started", ...}
#   {"ts": ..., "group": ..., "stage": ..., "event": "install|test", "module": ..., "rc": N}
# Exit 0 when every stage of every group is done (or was done before), 1 otherwise, 2 on usage errors.
#
# Groups file: one group per line, whitespace separated (no spaces in paths), '#' comments:
#   NAME SOURCE_DIR MODULE[,MODULE...] [REQUIREMENTS_FILE[,...]] [BASELINE_FREEZE_FILE]
# NAME is lowercase letters, digits and '-'; modules are listed in install (dependency) order;
# BASELINE_FREEZE_FILE is a results/requirements-freeze.txt recorded on --from, replayed as pins.
#
# Usage: migration-runner.sh --groups FILE --from 19 --to 20 --out DIR
#          [--stages "baseline plan code test verify"] [--agent codex|claude] [--model M]
#          [--stage-budget-usd N] [--group-budget-seconds N] [--stage-timeout SECONDS] [--parallel]
#          [--rerun "STAGE ..."]   (run these stages again even when an earlier run finished them)
# Environment: SANDBOXCTL, SANDBOX_SESSIONS_DIR and AGENT_CMD (the agent command; the prompt is
# appended as its last argument) override the kit defaults.
set -u

KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SANDBOXCTL=${SANDBOXCTL:-$KIT/sandbox/bin/sandboxctl}
SESSIONS=${SANDBOX_SESSIONS_DIR:-$KIT/.sandbox/sessions}
GROUPS_FILE="" FROM="" TO="" OUT="" STAGES="baseline plan code test verify" AGENT=codex MODEL=""
STAGE_BUDGET_USD="" GROUP_BUDGET_SECONDS="" STAGE_TIMEOUT=3600 PARALLEL=0 RERUN=""

usage() { echo "migration-runner: $*" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --groups) GROUPS_FILE=${2:-}; shift 2;;
    --from) FROM=${2:-}; shift 2;;
    --to) TO=${2:-}; shift 2;;
    --out) OUT=${2:-}; shift 2;;
    --stages) STAGES=${2:-}; shift 2;;
    --agent) AGENT=${2:-}; shift 2;;
    --model) MODEL=${2:-}; shift 2;;
    --stage-budget-usd) STAGE_BUDGET_USD=${2:-}; shift 2;;
    --group-budget-seconds) GROUP_BUDGET_SECONDS=${2:-}; shift 2;;
    --stage-timeout) STAGE_TIMEOUT=${2:-}; shift 2;;
    --parallel) PARALLEL=1; shift;;
    --rerun) RERUN=${2:-}; shift 2;;
    -h|--help) sed -n '2,/^set -u/p' "${BASH_SOURCE[0]}" | sed -e '$d' -e 's/^# \{0,1\}//'; exit 0;;
    *) usage "unknown argument: $1";;
  esac
done
[ -n "$GROUPS_FILE" ] && [ -f "$GROUPS_FILE" ] || usage "--groups FILE is required"
[[ "$FROM" =~ ^[0-9]+$ && "$TO" =~ ^[0-9]+$ ]] || usage "--from and --to take a major Odoo version (e.g. 19 20)"
[ -n "$OUT" ] || usage "--out DIR is required"
case "$AGENT" in codex|claude) ;; *) usage "--agent is codex or claude";; esac
for stage in $STAGES; do
  case "$stage" in baseline|plan|code|test|verify) ;; *) usage "unknown stage: $stage";; esac
done
[ -z "$GROUP_BUDGET_SECONDS" ] || [[ "$GROUP_BUDGET_SECONDS" =~ ^[0-9]+$ ]] || usage "--group-budget-seconds takes whole seconds"
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
QUOTA_FLAG=$OUT/.quota_stop
rm -f "$QUOTA_FLAG"

if [ -n "${AGENT_CMD:-}" ]; then
  read -r -a AGENT_ARGV <<< "$AGENT_CMD"
elif [ "$AGENT" = codex ]; then
  AGENT_ARGV=(codex exec --skip-git-repo-check)
else
  AGENT_ARGV=(claude -p --plugin-dir "$KIT/plugin" --dangerously-skip-permissions)
  [ -n "$MODEL" ] && AGENT_ARGV+=(--model "$MODEL")
  [ -n "$STAGE_BUDGET_USD" ] && AGENT_ARGV+=(--max-budget-usd "$STAGE_BUDGET_USD")
fi
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || true)

# emit GROUP key=value ... key:=JSON  -> one JSON line in OUT/GROUP/status.jsonl (and a short echo).
emit() {
  local group=$1; shift
  python3 - "$OUT/$group/status.jsonl" "$group" "$@" <<'PY'
import datetime, json, sys
path, group, pairs = sys.argv[1], sys.argv[2], sys.argv[3:]
line = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "group": group}
for pair in pairs:
    if ":=" in pair and pair.index(":=") < pair.find("=") + 1:
        key, value = pair.split(":=", 1)
        line[key] = json.loads(value)
    else:
        key, value = pair.split("=", 1)
        line[key] = value
with open(path, "a") as handle:
    handle.write(json.dumps(line) + "\n")
print(f"[{group}] " + " ".join(f"{k}={v}" for k, v in line.items() if k not in ("ts", "group", "message")), flush=True)
PY
}

stage_done() {  # GROUP STAGE -> 0 when a "done" line exists for the stage
  python3 - "$OUT/$1/status.jsonl" "$2" <<'PY'
import json, sys
try:
    lines = [json.loads(line) for line in open(sys.argv[1])]
except OSError:
    lines = []
sys.exit(0 if any(l.get("stage") == sys.argv[2] and l.get("status") == "done" for l in lines) else 1)
PY
}

agent_seconds_used() {  # GROUP -> sum of agent_seconds over the group's status lines
  python3 - "$OUT/$1/status.jsonl" <<'PY'
import json, sys
try:
    print(sum(int(json.loads(line).get("agent_seconds", 0)) for line in open(sys.argv[1])))
except OSError:
    print(0)
PY
}

json_field() {  # FILE KEY -> the JSON value of a top-level key (true/false/number/"string")
  python3 -c 'import json, sys; print(json.dumps(json.load(open(sys.argv[1])).get(sys.argv[2])))' "$1" "$2" 2>/dev/null || echo null
}

session_name() {  # PREFIX GROUP -> a valid, unique sandboxctl session ID
  echo "$1-$2-$(date +%H%M%S)-$RANDOM" | tr -c 'a-z0-9-\n' '-' | cut -c1-63
}

# install_and_test GROUP STAGE SESSION MODULES... : install every module in order, then test each;
# one status line per install/test; the session's Odoo log is kept as OUT/GROUP/STAGE-odoo.log.
install_and_test() {
  local group=$1 stage=$2 session=$3 module rc; shift 3
  INSTALL_EXITS=()
  for module in "$@"; do
    "$SANDBOXCTL" module "$session" install "$module" > "$OUT/$group/$stage-install-$module.log" 2>&1; rc=$?
    emit "$group" stage="$stage" event=install module="$module" rc:="$rc"
    INSTALL_EXITS+=("$module=$rc")
  done
  for module in "$@"; do
    "$SANDBOXCTL" module "$session" test "$module" > "$OUT/$group/$stage-test-$module.log" 2>&1; rc=$?
    emit "$group" stage="$stage" event=test module="$module" rc:="$rc"
  done
  cp "$SESSIONS/$session/logs/odoo.log" "$OUT/$group/$stage-odoo.log" 2>/dev/null || : > "$OUT/$group/$stage-odoo.log"
}

# gate GROUP EVENT PROMPT TAG -> the kit hook's exit code (2 = blocked); message in OUT/GROUP/gate-TAG.txt
gate() {
  local group=$1 event=$2 prompt=$3 tag=$4 repo=$OUT/$1/work
  python3 -c 'import json, sys; print(json.dumps({"cwd": sys.argv[1], "prompt": sys.argv[2]}))' "$repo" "$prompt" \
    | python3 "$KIT/plugin/hooks/odoo_hook.py" "$event" > "$OUT/$group/gate-$tag.txt" 2>&1
}

run_agent() {  # GROUP STAGE PROMPT -> agent exit code; output in OUT/GROUP/agent-STAGE.{out,err}
  local group=$1 stage=$2 prompt=$3 repo=$OUT/$1/work
  local -a limit=()
  [ -n "$TIMEOUT_BIN" ] && limit=("$TIMEOUT_BIN" "$STAGE_TIMEOUT")
  (cd "$repo" && RUNNER_STAGE=$stage ${limit[@]+"${limit[@]}"} "${AGENT_ARGV[@]}" "$prompt") \
    > "$OUT/$group/agent-$stage.out" 2> "$OUT/$group/agent-$stage.err"
}

quota_hit() {  # GROUP STAGE -> 0 when the agent reported a usage/quota limit
  grep -q -i -E "usage limit|quota exceeded|insufficient_quota|rate limit reached" "$OUT/$1/agent-$2.out" "$OUT/$1/agent-$2.err" 2>/dev/null
}

context() {  # GROUP SOURCE MODULES...
  local group=$1 source=$2; shift 2
  cat <<EOF
Non-interactive run: never ask questions; make and record reasonable decisions.
Work repository: $OUT/$group/work (git; tag 'baseline' = the untouched Odoo $FROM.0 sources). Modules, in dependency order: $*.
Goal: migrate all of them from Odoo $FROM.0 to Odoo $TO.0 Community.
Kit workflows (follow them as the definition of each step): $KIT/plugin/skills/CommandingSystem/SKILL.md and the workflow files
next to it; coding standard: $KIT/plugin/skills/Odoo${FROM}CodingStandard/SKILL.md (and the Odoo $TO.0 source in the session image).
Odoo runtime: $SANDBOXCTL only (never a raw odoo-bin):
- create: $SANDBOXCTL create --version $TO --module <first module> --import <a copy of the committed modules> [--requirements <file> ...] --session <name>
- install/update/test: $SANDBOXCTL module <session> install|update|test <module>; log: $SESSIONS/<session>/logs/odoo.log
- destroy: $SANDBOXCTL destroy <session> --allow-unexported
Baseline on $FROM.0: $OUT/$group/baseline-odoo.log. Success = every module installs on $TO.0 and
python3 $KIT/sandbox/scripts/test-parity.py $OUT/$group/baseline-odoo.log <your $TO.0 odoo.log> $(for m in "$@"; do printf -- '--expect-module %s ' "$m"; done)--install-exit <module>=<code> ... --json sessions/parity.json
exits 0. Record the outcome in sessions/<work repo name>_progress.json as start_coding_workflow.md describes, citing parity.json.
Commit your work with clear messages; never push. Keep secrets out of files and logs. Be economical.
EOF
}

stage_prompt() {  # STAGE -> the plain-words instruction (never a leading slash command, finding 2)
  case "$1" in
    plan) echo "Follow the kit workflow file $KIT/plugin/skills/CommandingSystem/plan_analysis_workflow.md (the plan-analysis step) for Odoo $TO: write the migration PRD (docs/requirements.md, docs/design.md, docs/tasks.md as a '- [ ] Task N:' checklist, docs/module_meta.md) in the work repository.";;
    code) echo "Follow the kit workflow file $KIT/plugin/skills/CommandingSystem/start_coding_workflow.md (the start-coding step) for Odoo $TO: execute every task in docs/tasks.md, with backend tests in a sandbox session after each task, and record the backend outcome.";;
    test) echo "Follow the kit workflow file $KIT/plugin/skills/CommandingSystem/testing_workflow.md (the testing step) for Odoo $TO: final install and tests of every migrated module versus the baseline, then the live UI check (sandbox/scripts/ui-check.py) and its \"ui_check\" record.";;
  esac
}

gate_command() {  # STAGE -> the slash command the kit's gates check for this stage
  case "$1" in code) echo "/start-coding $TO";; test) echo "/testing $TO";; *) echo "";; esac
}

agent_stage() {  # GROUP STAGE SOURCE MODULES...
  local group=$1 stage=$2 source=$3 started rc command prompt; shift 3
  if [ -n "$GROUP_BUDGET_SECONDS" ] && [ "$(agent_seconds_used "$group")" -ge "$GROUP_BUDGET_SECONDS" ]; then
    emit "$group" stage="$stage" status=budget_stop rc:=1 budget_seconds:="$GROUP_BUDGET_SECONDS" \
      used_seconds:="$(agent_seconds_used "$group")"
    return 1
  fi
  command=$(gate_command "$stage")
  if [ -n "$command" ] && ! gate "$group" UserPromptSubmit "$command" "$stage"; then
    emit "$group" stage="$stage" status=blocked rc:=2 message="$(tr '\n' ' ' < "$OUT/$group/gate-$stage.txt" | cut -c1-500)"
    return 1
  fi
  prompt="$(stage_prompt "$stage")

$(context "$group" "$source" "$@")"
  started=$SECONDS
  run_agent "$group" "$stage" "$prompt"; rc=$?
  if quota_hit "$group" "$stage"; then
    touch "$QUOTA_FLAG"
    emit "$group" stage="$stage" status=quota_stop rc:="$rc" agent_seconds:=$((SECONDS - started))
    return 1
  fi
  if [ -n "$command" ] && ! gate "$group" Stop "$prompt" "$stage-stop"; then
    run_agent "$group" "$stage-stop" "The kit's Stop gate blocked the end of this step with this message: $(cat "$OUT/$group/gate-$stage-stop.txt") Do exactly that now from what the last run showed, then stop.

$(context "$group" "$source" "$@")"
    if ! gate "$group" Stop "$prompt" "$stage-stop-after"; then
      emit "$group" stage="$stage" status=failed rc:=2 agent_seconds:=$((SECONDS - started)) \
        message="Stop gate still blocks: $(tr '\n' ' ' < "$OUT/$group/gate-$stage-stop-after.txt" | cut -c1-400)"
      return 1
    fi
  fi
  local commits
  commits=$(git -C "$OUT/$group/work" rev-list --count baseline..HEAD 2>/dev/null || echo 0)
  if [ "$rc" -eq 0 ]; then
    emit "$group" stage="$stage" status=done rc:=0 agent_seconds:=$((SECONDS - started)) commits:="$commits"
  else
    emit "$group" stage="$stage" status=failed rc:="$rc" agent_seconds:=$((SECONDS - started)) commits:="$commits"
  fi
  return "$rc"
}

requirement_flags() {  # FILES... -> --requirements FILE ...
  local file; for file in "$@"; do [ -n "$file" ] && printf -- '--requirements\n%s\n' "$file"; done
}

baseline_stage() {  # GROUP SOURCE REQS FREEZE MODULES...
  local group=$1 source=$2 reqs=$3 freeze=$4 session; shift 4
  local -a flags=()
  [ -n "$reqs" ] && while IFS= read -r flag; do flags+=("$flag"); done < <(requirement_flags ${reqs//,/ })
  [ -n "$freeze" ] && flags+=(--requirements-freeze "$freeze")
  session=$(session_name base "$group")
  if ! "$SANDBOXCTL" create --version "$FROM" --module "$1" --session "$session" --import "$source" ${flags[@]+"${flags[@]}"} \
      > "$OUT/$group/baseline-create.log" 2>&1; then
    emit "$group" stage=baseline status=failed rc:=1 message="create failed: $(tail -2 "$OUT/$group/baseline-create.log" | tr '\n' ' ' | cut -c1-300)"
    return 1
  fi
  install_and_test "$group" baseline "$session" "$@"
  "$SANDBOXCTL" destroy "$session" --allow-unexported > /dev/null 2>&1
  emit "$group" stage=baseline status=done rc:=0 session="$session"
}

verify_stage() {  # GROUP REQS MODULES...
  local group=$1 reqs=$2 session tree rc dirty module; shift 2
  local repo=$OUT/$group/work
  if [ ! -s "$OUT/$group/baseline-odoo.log" ]; then
    emit "$group" stage=verify status=failed rc:=1 message="no baseline log: run the baseline stage first"
    return 1
  fi
  dirty=$(git -C "$repo" status --porcelain | wc -l | tr -d ' ')
  tree=$OUT/$group/verify-tree-$(date +%Y%m%d%H%M%S)
  mkdir -p "$tree" && git -C "$repo" archive HEAD | tar -x -C "$tree"
  local -a flags=()
  # Word splitting is intended: the groups file forbids spaces in paths, and the staged tree is ours.
  # shellcheck disable=SC2046
  while IFS= read -r flag; do flags+=("$flag"); done < <(requirement_flags ${reqs//,/ } $(find "$tree" -mindepth 2 -maxdepth 2 -name requirements.txt | sort))
  session=$(session_name verify "$group")
  if ! "$SANDBOXCTL" create --version "$TO" --module "$1" --session "$session" --import "$tree" ${flags[@]+"${flags[@]}"} \
      > "$OUT/$group/verify-create.log" 2>&1; then
    emit "$group" stage=verify status=failed rc:=1 message="create failed: $(tail -2 "$OUT/$group/verify-create.log" | tr '\n' ' ' | cut -c1-300)"
    return 1
  fi
  install_and_test "$group" verify "$session" "$@"
  local -a parity=()
  for module in "$@"; do parity+=(--expect-module "$module"); done
  for module in "${INSTALL_EXITS[@]}"; do parity+=(--install-exit "$module"); done
  python3 "$KIT/sandbox/scripts/test-parity.py" "$OUT/$group/baseline-odoo.log" "$OUT/$group/verify-odoo.log" \
    "${parity[@]}" --json "$OUT/$group/parity.json" > "$OUT/$group/parity.txt" 2>&1; rc=$?
  "$SANDBOXCTL" destroy "$session" --allow-unexported > /dev/null 2>&1
  local status="done"; [ "$rc" -eq 0 ] || status=failed
  emit "$group" stage=verify status="$status" rc:="$rc" head="$(git -C "$repo" rev-parse --short HEAD)" \
    uncommitted_files:="$dirty" parity:="$(json_field "$OUT/$group/parity.json" parity)" pass:="$(json_field "$OUT/$group/parity.json" pass)"
  return "$rc"
}

run_group() {  # NAME SOURCE MODULES REQS FREEZE
  local group=$1 source=$2 modules=${3//,/ } reqs=$4 freeze=$5 stage rc=0
  mkdir -p "$OUT/$group"
  local repo=$OUT/$group/work
  if [ ! -d "$repo/.git" ]; then
    mkdir -p "$repo" && cp -a "$source/." "$repo/" && rm -rf "$repo/.git"
    git -C "$repo" init -q && git -C "$repo" add -A \
      && git -C "$repo" -c user.name=migration-runner -c user.email=migration-runner@localhost commit -qm "Odoo $FROM.0 baseline" \
      && git -C "$repo" tag baseline
  fi
  for stage in $STAGES; do
    if [[ " $RERUN " != *" $stage "* ]] && stage_done "$group" "$stage"; then
      emit "$group" stage="$stage" status=skipped reason="done in an earlier run"
      continue
    fi
    if [ -e "$QUOTA_FLAG" ]; then
      emit "$group" stage="$stage" status=not_started reason="agent quota exhausted in this batch"
      return 1
    fi
    case "$stage" in
      baseline) baseline_stage "$group" "$source" "$reqs" "$freeze" $modules || return 1;;
      verify) verify_stage "$group" "$reqs" $modules || return 1;;
      *) agent_stage "$group" "$stage" "$source" $modules || return 1;;
    esac
  done
  return "$rc"
}

declare -a NAMES=() SOURCES=() MODULE_LISTS=() REQUIREMENTS=() FREEZES=()
while read -r name source modules reqs freeze _; do
  [ -z "${name:-}" ] || [[ "$name" == \#* ]] && continue
  [[ "$name" =~ ^[a-z0-9][a-z0-9-]{0,30}$ ]] || usage "invalid group name: $name"
  [ -d "${source:-}" ] || usage "group $name: source is not a directory: ${source:-}"
  [[ "${modules:-}" =~ ^[a-z][a-z0-9_]*(,[a-z][a-z0-9_]*)*$ ]] || usage "group $name: modules must be a comma-separated list"
  NAMES+=("$name"); SOURCES+=("$(cd "$source" && pwd)"); MODULE_LISTS+=("$modules"); REQUIREMENTS+=("${reqs:-}"); FREEZES+=("${freeze:-}")
done < "$GROUPS_FILE"
[ "${#NAMES[@]}" -gt 0 ] || usage "no groups in $GROUPS_FILE"

failed=0
if [ "$PARALLEL" = 1 ]; then
  pids=()
  for i in "${!NAMES[@]}"; do
    run_group "${NAMES[$i]}" "${SOURCES[$i]}" "${MODULE_LISTS[$i]}" "${REQUIREMENTS[$i]}" "${FREEZES[$i]}" & pids+=($!)
  done
  for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
else
  for i in "${!NAMES[@]}"; do
    run_group "${NAMES[$i]}" "${SOURCES[$i]}" "${MODULE_LISTS[$i]}" "${REQUIREMENTS[$i]}" "${FREEZES[$i]}" || failed=1
  done
fi
exit "$failed"
