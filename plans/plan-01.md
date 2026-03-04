# Plan 01 - Bootstrap peanut-openclaw (todo + note MCP first)

## Goal
Set up a new repo at `~/data/code/peanut-openclaw` with:
1. A working MCP server exposing **todo** and **note** tools.
2. Deployment setup that survives reboot.
3. Initial deployment + smoke tests.
4. Environment copied from old Peanut repo.

## Scope (this iteration)
- In scope:
  - Repo scaffolding
  - MCP server for todo + note only
  - Microsoft To Do integration (create task, set my day)
  - Note integration (save/find/all) via Mongo
  - `mcporter` registration and call tests
  - Reboot-safe deployment approach
- Out of scope:
  - FUNiX migration
  - Telegram command routing
  - AI classifier/router

## Architecture decisions
- Use **one MCP server** first (`peanut-mcp`) for faster delivery.
- Implement MCP in **Node.js** (`@modelcontextprotocol/sdk`) as runtime boundary.
- Reuse existing Peanut Python logic via a local **Python bridge module** to reduce risk and migration time.
- Use `mcporter` stdio config (home scope) with absolute command path so it remains callable after reboot.

## Implementation steps
- [x] Step 1: Create repository structure + package metadata.
- [x] Step 2: Copy env file from old repo (`Peanut/scripts/.env`) into new repo.
- [x] Step 3: Add Python bridge package:
  - [x] todo APIs (token manager, graph API, create_task, set_my_day)
  - [x] note APIs (mongo connection + DAO)
  - [x] CLI entrypoint returning JSON for MCP server
- [x] Step 4: Build Node MCP server with tools:
  - [x] `todo_create_task`
  - [x] `todo_set_my_day`
  - [x] `note_save`
  - [x] `note_find`
  - [x] `note_all`
- [x] Step 5: Add install/deploy scripts.
- [x] Step 6: Register MCP server in `mcporter` config (home scope).
- [x] Step 7: Run smoke tests through `mcporter call` for todo + note tools.
- [x] Step 8: Update this plan with outcomes + open issues.

## Test checklist
- [x] `mcporter list peanut-mcp --schema` shows tool schema.
- [x] `note_save` works and returns note id.
- [x] `note_find` returns saved note.
- [x] `todo_create_task` creates task in expected list.
- [x] `todo_set_my_day` returns summary string.

## Outcomes
- New repo scaffolded at `~/data/code/peanut-openclaw`.
- `.env` copied from old Peanut repo.
- MCP server `peanut-mcp` deployed via `mcporter` in **home** scope.
- Smoke tests passed for todo + note via `mcporter call`.
- Note persistence supports Mongo first, with local JSON fallback for environments where Mongo write auth is blocked.

## Open issues / next steps
- Migrate FUNiX tools into this MCP (phase 2).
- Decide whether to keep file fallback for notes in production or enforce Mongo-only.
- Add CI workflow to run `scripts/deploy.sh` + smoke tests automatically.

## Reboot resilience
- `mcporter` home config persists across reboot.
- MCP command references absolute paths in the new repo.
- `deploy.sh` supports idempotent reinstall/reconfigure.

## Notes
- Keep credentials in `.env` only (do not commit secrets).
- Add `.gitignore` and `.env.example`.
