#!/usr/bin/env bash
set -euo pipefail

session="${1:-phase6-primary}"
state=".sandbox/sessions/$session"
ctl="sandbox/bin/sandboxctl"
compose=(docker compose --env-file "$state/runtime.env" -f sandbox/compose/compose.yaml)

# psql FLAGS SQL — exec into the db container, or in run mode (Docker Cloud Sandboxes, where
# `docker exec` does not work) a one-shot client over the Compose network.
psql_db() {
  if [ "$(sed -n 's/^SANDBOX_EXEC_MODE=//p' "$state/runtime.env")" = "run" ]; then
    "${compose[@]}" run --rm --no-deps -T -e PHASE6_SQL="$2" db sh -c \
      'PGPASSWORD="$POSTGRES_PASSWORD" psql -h db '"$1"' -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$PHASE6_SQL"'
  else
    "${compose[@]}" exec -T -e PHASE6_SQL="$2" db sh -c \
      'psql '"$1"' -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$PHASE6_SQL"'
  fi
}

psql_db "" "DROP TABLE IF EXISTS phase6_restore_probe; CREATE TABLE phase6_restore_probe(value text); INSERT INTO phase6_restore_probe VALUES ('baseline');"
backup="$($ctl backup "$session" | tail -1)"
psql_db "" "INSERT INTO phase6_restore_probe VALUES ('after-backup');"
"$ctl" restore "$session" "$backup"
count="$(psql_db -At "SELECT count(*) FROM phase6_restore_probe")"
test "$count" = 1

telemetry="$PWD/$state/logs/otel.jsonl"
SANDBOX_OTEL_LOG_ENDPOINT="file://$telemetry" "$ctl" diagnose "$session" --reason telemetry-proof >/dev/null
test -s "$telemetry"

first_line="$($ctl logs "$session" --service odoo --since 5m | head -1)"
case "$first_line" in
  "[$session/19.0/sandbox_fixture/odoo]"*) ;;
  *) echo "unexpected log prefix: $first_line" >&2; exit 1 ;;
esac

echo "BACKUP_RESTORE=passed"
echo "TELEMETRY=passed"
echo "LOG_PREFIX=passed"
