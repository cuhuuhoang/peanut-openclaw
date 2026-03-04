#!/usr/bin/env bash
set -euo pipefail

TZ_NAME="${TZ_NAME:-Asia/Saigon}"
TARGET_CHANNEL="${TARGET_CHANNEL:-telegram}"
TARGET_TO="${TARGET_TO:-1045833166}"

FUNIX_JOB_NAME="peanut-funix-weekly-slots"
TUTOR_JOB_NAME="peanut-weekly-tutor-todo"

remove_job_by_name() {
  local name="$1"
  local ids
  local json
  json="$(openclaw cron list --json)"
  ids=$(python3 - "$name" "$json" <<'PY'
import json,sys
name = sys.argv[1]
data = json.loads(sys.argv[2])
for job in data.get("jobs", []):
    if job.get("name") == name:
        print(job.get("jobId") or job.get("id"))
PY
)

  if [ -n "${ids:-}" ]; then
    while IFS= read -r id; do
      [ -z "$id" ] && continue
      openclaw cron rm "$id" >/dev/null
      echo "[ok] removed old job $name ($id)"
    done <<< "$ids"
  fi
}

remove_job_by_name "$FUNIX_JOB_NAME"
remove_job_by_name "$TUTOR_JOB_NAME"

FUNIX_MSG="Run this command exactly and summarize result in Vietnamese:\nmcporter call peanut-mcp.funix_create_weekly_slots --args '{}'\nIf it fails, report the exact error."
TUTOR_MSG="Run this command exactly and summarize result in Vietnamese:\nmcporter call peanut-mcp.todo_create_weekly_tutor --args '{\"listName\":\"Funix\"}'\nIf it fails, report the exact error."

openclaw cron add \
  --name "$FUNIX_JOB_NAME" \
  --cron "25 7 * * 1" \
  --tz "$TZ_NAME" \
  --session isolated \
  --message "$FUNIX_MSG" \
  --announce \
  --channel "$TARGET_CHANNEL" \
  --to "$TARGET_TO" \
  --best-effort-deliver >/dev/null

echo "[ok] added $FUNIX_JOB_NAME"

openclaw cron add \
  --name "$TUTOR_JOB_NAME" \
  --cron "25 7 * * 1" \
  --tz "$TZ_NAME" \
  --session isolated \
  --message "$TUTOR_MSG" \
  --announce \
  --channel "$TARGET_CHANNEL" \
  --to "$TARGET_TO" \
  --best-effort-deliver >/dev/null

echo "[ok] added $TUTOR_JOB_NAME"

echo "[ok] current cron jobs"
openclaw cron list --json
