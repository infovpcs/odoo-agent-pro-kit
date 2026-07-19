#!/usr/bin/env bash
# PreCompact hook: snapshot lightweight task progress before context is summarized.
# No-ops when there's no docs/tasks.md (not in an active /start-coding workspace).
set -uo pipefail

TASKS_FILE="./docs/tasks.md"

if [ ! -f "$TASKS_FILE" ]; then
  exit 0
fi

SESSIONS_DIR="./sessions"
mkdir -p "$SESSIONS_DIR"

MODULE_NAME="$(basename "$(pwd)")"
OUT_FILE="$SESSIONS_DIR/${MODULE_NAME}_progress.json"

TOTAL=$(grep -c '^- \[' "$TASKS_FILE" 2>/dev/null || echo 0)
DONE=$(grep -c '^- \[x\]' "$TASKS_FILE" 2>/dev/null || echo 0)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$OUT_FILE" <<EOF
{
  "module": "$MODULE_NAME",
  "tasks_total": $TOTAL,
  "tasks_done": $DONE,
  "snapshot_at": "$TIMESTAMP"
}
EOF

echo "[odoo-agent-pro-kit] Progress snapshot saved to $OUT_FILE ($DONE/$TOTAL tasks done)"
exit 0
