#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Schema =="
mcporter list peanut-mcp --schema >/dev/null

echo "== note_save =="
SAVE_OUT=$(mcporter call peanut-mcp.note_save --args '{"title":"peanut-openclaw smoke","content":"hello from smoke test","tags":["openclaw","smoke"]}')
echo "$SAVE_OUT"

echo "== note_find =="
mcporter call peanut-mcp.note_find --args '{"query":"peanut-openclaw smoke"}'

echo "== todo_create_task =="
NOW_PLUS_30=$(python3 - <<'PY'
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
print((datetime.now(ZoneInfo('Asia/Bangkok')) + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S'))
PY
)
mcporter call peanut-mcp.todo_create_task --args "{\"listName\":\"Personal\",\"title\":\"[smoke] peanut-openclaw todo\",\"remind\":\"$NOW_PLUS_30\",\"subTasks\":[\"verify mcp\"]}"

echo "== todo_set_my_day =="
mcporter call peanut-mcp.todo_set_my_day --args '{}'

echo "[ok] smoke tests completed"
