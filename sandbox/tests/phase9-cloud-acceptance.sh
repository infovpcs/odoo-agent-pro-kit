#!/usr/bin/env bash
# Phase 9: Phase 7 clean-host acceptance steps 1, 2-3, 4, 5, 6 and 8 inside one Docker Cloud
# Sandbox (see docs/docker-sandbox/phase-9/cloud-runbook.md). Step 7 (agent CLIs/SSH) needs
# agent credentials and runs separately. Every step records PASS/FAIL and the run continues,
# so one billed run yields the whole matrix; the exit code is non-zero if any step failed.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
export SANDBOX_EXEC_MODE=run
CTL=sandbox/bin/sandboxctl
OUT="${PHASE9_EVIDENCE_DIR:-.sandbox/release/phase9}"
BENCH=(python3 sandbox/scripts/benchmark.py --output "$OUT/benchmarks.jsonl")
mkdir -p "$OUT"
: > "$OUT/steps.txt"
failed=0

step() {
  local name="$1"; shift
  local started=$SECONDS rc
  echo "=== STEP $name"
  "$@"; rc=$?
  local verdict=PASS; [ "$rc" -eq 0 ] || { verdict=FAIL; failed=1; }
  printf '%s %s rc=%s %ss\n' "$verdict" "$name" "$rc" "$((SECONDS - started))" | tee -a "$OUT/steps.txt"
}

healthy() {
  "$CTL" status "$1" | python3 -c 'import json,sys; v=json.load(sys.stdin); assert v["status"] in {"ready","recoverable"}, v["status"]; assert len(v["services"]) == 2 and all(r.get("Health") == "healthy" for r in v["services"]), v["services"]'
}

session_psql() {  # SESSION SQL — one-shot client, prints the unaligned result
  local env_file=".sandbox/sessions/$1/runtime.env"
  docker compose --env-file "$env_file" -f sandbox/compose/compose.yaml run --rm --no-deps -T -e PHASE9_SQL="$2" db \
    sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -h db -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$PHASE9_SQL"'
}

preflight() {
  { uname -a; nproc; free -b; df -B1 /; docker version; docker compose version; python3 --version; } > "$OUT/platform.txt" 2>&1 &&
  python3 sandbox/scripts/release-acceptance.py verify &&
  sandbox/scripts/validate-compose.sh &&
  python3 sandbox/scripts/dependency-inventory.py --output "$OUT/dependencies.json"
}

warm_create_19() {
  "${BENCH[@]}" --label warm -- "$CTL" create --version 19 --module sandbox_fixture --session warm19 &&
  healthy warm19 &&
  "$CTL" destroy warm19 --allow-unexported
}

SIX=(phase6-primary:19 s6-19b:19 s6-17a:17 s6-17b:17 s6-18a:18 s6-18b:18)

create_six() {
  local pids=() entry rc=0
  for entry in "${SIX[@]}"; do
    "$CTL" create --version "${entry#*:}" --module sandbox_fixture --session "${entry%%:*}" > "$OUT/create-${entry%%:*}.log" 2>&1 &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do wait "$pid" || rc=1; done
  { free -b; docker stats --no-stream --format '{{json .}}'; } > "$OUT/six-session-resources.txt" 2>&1
  return "$rc"
}

denied_network() {
  local policy="$OUT/denied-network.txt" code
  command -v curl >/dev/null || { echo "curl missing"; return 1; }
  code="$(curl -sS -m 15 -o /dev/null -w '%{http_code}' https://example.com 2>>"$policy")"
  echo "https://example.com -> http_code=${code:-none}" >> "$policy"
  "$CTL" diagnose phase6-primary --reason denied-network --policy-file "$policy" >/dev/null
  case "$code" in 2??) return 1 ;; esac  # a 2xx would mean the default-deny policy let it through
}

siblings_healthy() {
  local entry
  for entry in "${SIX[@]:1}"; do healthy "${entry%%:*}" || { echo "unhealthy sibling ${entry%%:*}"; return 1; }; done
  echo "SIBLING_HEALTH=passed"
}

destroy_siblings() {
  local entry
  for entry in "${SIX[@]:1}"; do "$CTL" destroy "${entry%%:*}" --allow-unexported || return 1; done
}

restore_into_new_session() {
  local backup
  backup="$("$CTL" backup phase6-primary | tail -1)" &&
  "$CTL" create --version 19 --module sandbox_fixture --session restore19 &&
  # restore only accepts the target session's own artifacts: import the backup explicitly first.
  cp "$backup" ".sandbox/sessions/restore19/backups/" &&
  "$CTL" restore restore19 ".sandbox/sessions/restore19/backups/$(basename "$backup")" &&
  healthy restore19 &&
  test "$(session_psql restore19 'SELECT count(*) FROM phase6_restore_probe')" = 1
}

migrate_local() {
  local source work
  work="$(mktemp -d)"; source="$work/custom-addons"
  mkdir -p "$source" && cp -R sandbox/fixtures/sandbox_fixture "$source/mig_fixture" &&
  echo "API_TOKEN=phase9-not-a-real-secret" > "$source/.env" &&
  git -C "$source" init -q && git -C "$source" add -A &&
  git -C "$source" -c user.name=phase9 -c user.email=phase9@example.invalid commit -qm fixture &&
  python3 sandbox/scripts/migrate-local.py --source "$source" --version 19 --name mig_fixture --output-root "$OUT/imports" > "$OUT/migration.json" &&
  python3 - "$OUT/imports/19-mig_fixture" <<'PY'
import json, pathlib, sys
target = pathlib.Path(sys.argv[1])
report = json.loads((target / "migration-report.json").read_text())
assert report["secrets_copied"] is False
assert not (target / ".git").exists() and not (target / ".env").exists()
assert (target / "mig_fixture/__manifest__.py").exists()
print("MIGRATION=passed")
PY
}

destroy_all_and_prove_clean() {
  local session
  for session in $(ls .sandbox/sessions 2>/dev/null); do
    "$CTL" destroy "$session" --allow-unexported || return 1
  done
  { docker ps -a; docker volume ls; docker network ls; ss -ltn 2>/dev/null || true; } > "$OUT/final-state.txt"
  test -z "$(docker ps -aq)" &&
  test -z "$(docker volume ls -q)" &&
  test -z "$(docker network ls --format '{{.Name}}' | grep -vxE 'bridge|host|none')"
}

step 1-preflight preflight
step 2-cold-lifecycle "${BENCH[@]}" --label cold -- bash sandbox/tests/lifecycle.sh
step 3-warm-lifecycle "${BENCH[@]}" --label warm -- bash sandbox/tests/lifecycle.sh
step 3-warm-create-19 warm_create_19
step 4-six-sessions "${BENCH[@]}" --label six-session -- bash -c "$(declare -p SIX CTL OUT); $(declare -f create_six); create_six"
step 4-phase6-live "${BENCH[@]}" --label recovery -- bash sandbox/tests/phase6-live.sh phase6-primary sandbox_fixture
step 4-phase6-proof bash sandbox/tests/phase6-proof.sh phase6-primary
step 4-denied-network denied_network
step 4-phase6-verify python3 sandbox/tests/phase6-verify.py phase6-primary
step 4-siblings-healthy siblings_healthy
step 4-destroy-siblings destroy_siblings
step 5-upgrade-rollback python3 sandbox/tests/upgrade-rollback.py
step 5-restore-new-session restore_into_new_session
step 6-migrate-local migrate_local
step 8-destroy-all-clean destroy_all_and_prove_clean

echo "=== SUMMARY"
cat "$OUT/steps.txt"
exit "$failed"
