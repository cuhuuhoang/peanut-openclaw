# peanut-openclaw

OpenClaw migration project for Peanut bot logic.

This repository provides a custom MCP server (`peanut-mcp`) that exposes To Do, Note, and FUNiX automation as tools callable from OpenClaw (and from `mcporter`).

## Features

### To Do tools
- `todo_create_task`
- `todo_set_my_day`
- `todo_create_weekly_tutor`

### Note tools
- `note_save`
- `note_find`
- `note_all`

### FUNiX tools
- `funix_extract_session_from_url`
- `funix_create_todo_from_url`
- `funix_create_weekly_slots`

## Repository layout

- `src/server.mjs` — Node MCP server (stdio transport)
- `peanut_bridge/` — Python bridge layer (Microsoft To Do, FUNiX, Notes)
- `scripts/install.sh` — install Python + Node dependencies
- `scripts/deploy.sh` — deploy/register `peanut-mcp` via `mcporter`
- `scripts/deploy-cron.sh` — create/update weekly OpenClaw cron jobs
- `scripts/test-smoke.sh` — smoke tests for MCP tools
- `plans/` — implementation plans and progress notes

## Prerequisites

- Node.js (v20+ recommended)
- Python 3.11+
- `mcporter` CLI installed and available in `PATH`
- OpenClaw CLI installed (`openclaw`)

## Environment setup

1. Copy environment template:

```bash
cp .env.example .env
```

2. Fill required values in `.env`:

- Microsoft To Do:
  - `MICROSOFT_CLIENT_ID`
  - `MICROSOFT_CLIENT_SECRET` (optional depending on account/app)
  - `MICROSOFT_TENANT_ID` (default: `consumers`)
  - `MICROSOFT_ACCESS_TOKEN`
  - `MICROSOFT_REFRESH_TOKEN`

- Mongo (notes):
  - `MONGO_USER`
  - `MONGO_PASS`
  - `MONGO_HOST`
  - `MONGO_PORT`
  - `MONGO_DB`
  - `MONGO_AUTH_DB`

- FUNiX:
  - `FUNIX_SESSION_ID`
  - `FUNIX_MENTOR_ID` (default supported)
  - `FUNIX_UID` (default supported)

Optional:
- `DATA_DIR`

## Deploy MCP server

```bash
bash scripts/deploy.sh
```

What this does:
- Creates/updates Python virtualenv
- Installs Python + Node dependencies
- Registers `peanut-mcp` in **home-scope** mcporter config
  (`~/.mcporter/mcporter.json`) with absolute paths

This makes MCP registration persistent across reboot.

## Test MCP tools

```bash
bash scripts/test-smoke.sh
```

Optional env flags:
- `FUNIX_TEST_URL=<portal_link>` to run live FUNiX extract/todo test
- `RUN_WEEKLY_SIDE_EFFECTS=1` to run weekly side-effect tools during smoke test

## Deploy weekly cron jobs (OpenClaw)

```bash
bash scripts/deploy-cron.sh
```

By default, this script creates/updates 2 jobs:
- `peanut-funix-weekly-slots`
- `peanut-weekly-tutor-todo`

Schedule:
- Monday, `07:25`, timezone `Asia/Saigon`

Default delivery target:
- channel: `telegram`
- to: `1045833166`

Override target when needed:

```bash
TARGET_CHANNEL=telegram TARGET_TO=<your_chat_id> bash scripts/deploy-cron.sh
```

## Useful commands

```bash
# list MCP tool schema
mcporter list peanut-mcp --schema

# call a tool manually
mcporter call peanut-mcp.todo_set_my_day --args '{}'

# list cron jobs
openclaw cron list --json

# run a cron job now (debug)
openclaw cron run <job-id>
```

## Notes / operational cautions

- Do not commit `.env`, token files, or personal secrets.
- `data/tokens.json` stores refreshed Microsoft tokens locally.
- Notes currently support Mongo-first persistence with fallback handling in bridge code.
- FUNiX operations depend on valid `FUNIX_SESSION_ID`; if expired, FUNiX tools will fail.
- Weekly tools create real side effects (tasks/slots). Use smoke flags carefully.

## Reboot behavior

- MCP registration survives reboot (home-scope mcporter config + absolute command paths).
- OpenClaw cron jobs are stored by Gateway and also survive reboot.

---

If you need to re-provision from scratch on a new machine, run in order:
1. `bash scripts/deploy.sh`
2. `bash scripts/deploy-cron.sh`
3. `bash scripts/test-smoke.sh`
