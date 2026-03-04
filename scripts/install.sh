#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "[warn] .env not found in $ROOT_DIR"
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

./.venv/bin/pip install --upgrade pip >/dev/null
./.venv/bin/pip install -r requirements.txt >/dev/null

npm install --silent

echo "[ok] install complete"
