# Plan 02 - Add FUNiX MCP tools + chain to To Do

## Goal
Extend `peanut-mcp` with FUNiX capability and end-to-end tool flow:
- Parse FUNiX portal URL
- Fetch/parse session info from FUNiX API
- (Optional) create Microsoft To Do reminder from extracted session

## Scope (this iteration)
- In scope:
  - Migrate FUNiX extraction logic from old Peanut bot
  - Expose FUNiX as MCP tools
  - Add one-chain tool for convenience (`funix_create_todo_from_url`)
  - Deploy + smoke test
- Out of scope:
  - Telegram routing and message handlers
  - AI classifier policies

## Tool design
- `funix_extract_session_from_url`
  - Input: `{ "url": "https://portal.funix.edu.vn/web#id=...&model=..." }`
  - Output: structured session object + computed reminder time
- `funix_create_todo_from_url`
  - Input: `{ "url": "...", "listName": "Funix" }`
  - Flow: extract -> build todo payload -> call todo_create_task backend
  - Output: extraction data + todo result message

## Implementation checklist
- [x] Add `peanut_bridge/funix_api.py` with parsing + API fetch + task payload builder
- [x] Extend `peanut_bridge/cli.py` actions for FUNiX tools
- [x] Extend `src/server.mjs` tool schemas + dispatcher
- [x] Add smoke test entries for FUNiX tools
- [x] Redeploy MCP and run smoke tests
- [x] Update this plan with outcomes/open issues

## Risk notes
- FUNiX API depends on valid `FUNIX_SESSION_ID` in `.env`.
- If session expired, extraction tool should return clear error, not crash.

## Acceptance criteria
- `mcporter call peanut-mcp.funix_extract_session_from_url ...` returns structured JSON or controlled error.
- `mcporter call peanut-mcp.funix_create_todo_from_url ...` can create a To Do task when FUNIX session is valid.
- Existing `todo_*` and `note_*` tools remain working.

## Outcomes
- Added FUNiX bridge module with URL parsing, portal API fetch, zoom-summary extraction, and reminder window validation.
- Added MCP tools:
  - `funix_extract_session_from_url`
  - `funix_create_todo_from_url`
- Improved MCP error behavior to return controlled tool errors (`isError`) instead of transport failures.
- Redeployed MCP and verified:
  - Existing todo/note smoke tests pass.
  - FUNiX tool appears in schema.
  - Invalid URL returns controlled JSON error.
- FUNiX live smoke remains optional and is wired via `FUNIX_TEST_URL` env var in `scripts/test-smoke.sh`.

## Open issues / next steps
- Run live FUNiX end-to-end test with a valid current portal URL (`FUNIX_TEST_URL`) to verify remote API/session validity.
- Consider replacing hard-coded cookie template in FUNiX headers with minimal required headers.
- Decide whether to keep one-chain tool (`funix_create_todo_from_url`) or force orchestration from OpenClaw side only.
