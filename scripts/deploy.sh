#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

bash "$ROOT_DIR/scripts/install.sh"

# Register stdio MCP server in home scope so config survives reboot.
mcporter config remove peanut-mcp >/dev/null 2>&1 || true
mcporter config add peanut-mcp \
  --scope home \
  --command node \
  --arg "$ROOT_DIR/src/server.mjs" \
  --env "PEANUT_OPENCLAW_ROOT=$ROOT_DIR" \
  --env "PEANUT_BRIDGE_PYTHON=$ROOT_DIR/.venv/bin/python3" \
  --env "PYTHONPATH=$ROOT_DIR" \
  --description "Peanut MCP (todo + note + funix)"

echo "[ok] deployed peanut-mcp"
mcporter config get peanut-mcp --json
