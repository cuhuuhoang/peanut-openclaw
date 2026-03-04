# peanut-openclaw

Custom MCP server for OpenClaw migration (phase 1): todo + note.

## Tools
- `todo_create_task`
- `todo_set_my_day`
- `note_save`
- `note_find`
- `note_all`
- `funix_extract_session_from_url`
- `funix_create_todo_from_url`

## Quick start
```bash
bash scripts/deploy.sh
bash scripts/test-smoke.sh
```

## Reboot behavior
Configured via `mcporter config add --scope home` with absolute paths.
After reboot, `mcporter call peanut-mcp.<tool>` works without manual re-register.
