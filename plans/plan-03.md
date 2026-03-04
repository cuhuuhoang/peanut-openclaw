# Plan 03 - Add weekly FUNiX/tutor tools + OpenClaw cron jobs

## Goal
Add the remaining weekly automation from Peanut into `peanut-openclaw`:
1. Weekly FUNiX available-slot creation ("lịch rảnh").
2. Weekly tutor To Do generation.
3. OpenClaw cron jobs to run both flows automatically.

## Scope
- In scope:
  - New MCP tools for weekly FUNiX slots and weekly tutor todos.
  - Deploy updated MCP server.
  - Programmatically create/update OpenClaw cron jobs.
  - Smoke checks for tools + cron registration.
- Out of scope:
  - Changing Telegram command handlers.
  - Reworking old FUNiX business rules.

## Design
- Keep one MCP server (`peanut-mcp`) and add tools:
  - `funix_create_weekly_slots`
  - `todo_create_weekly_tutor`
- Cron managed by OpenClaw (`openclaw cron add ...`) with isolated sessions.
- Cron task prompt will call MCP tools via `mcporter call` to keep runtime deterministic.

## Cron targets
- Job A: `peanut-funix-weekly-slots`
  - schedule: Monday 07:25 Asia/Saigon
  - action: run `funix_create_weekly_slots`
- Job B: `peanut-weekly-tutor-todo`
  - schedule: Monday 07:25 Asia/Saigon
  - action: run `todo_create_weekly_tutor`

## Checklist
- [x] Implement FUNiX weekly slots bridge logic.
- [x] Implement weekly tutor todo bridge logic.
- [x] Extend MCP CLI/server schemas for both tools.
- [x] Extend smoke tests.
- [x] Add cron deployment script (`scripts/deploy-cron.sh`).
- [x] Deploy MCP and cron jobs.
- [x] Validate jobs exist via `openclaw cron list --json`.
- [x] Update this plan with outcomes/open issues.

## Acceptance criteria
- `mcporter call peanut-mcp.funix_create_weekly_slots` returns report text.
- `mcporter call peanut-mcp.todo_create_weekly_tutor` returns creation summary.
- Cron list contains both weekly jobs with expected schedule.
- Existing tools remain functional.

## Outcomes
- Added MCP tools:
  - `funix_create_weekly_slots`
  - `todo_create_weekly_tutor`
- Added bridge modules/functions for both weekly flows.
- Added cron deployment script: `scripts/deploy-cron.sh`.
- Deployed two OpenClaw cron jobs (Monday 07:25 Asia/Saigon):
  - `peanut-funix-weekly-slots`
  - `peanut-weekly-tutor-todo`
- Verified cron registration with `openclaw cron list --json`.
- Existing smoke tests still pass (todo/note + base funix checks).

## Open issues / next steps
- Optional: run `openclaw cron run <jobId>` manually once for end-to-end dry validation at your chosen time.
- Optional hardening: deduplicate tutor todos per week to prevent accidental duplicates on manual reruns.
- Optional hardening: add a direct MCP execution runtime for cron (avoid relying on prompt text to run `mcporter call`).
