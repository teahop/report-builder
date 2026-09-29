#!/bin/bash
# Double-click to start the local production instance and open the operator UI.
# Requires .venv and .env.production in this folder.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f .env.production ]; then
  echo "Missing .env.production. Copy .env.production.example and fill in the keys."
  exit 1
fi

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export APP_PROFILE=production
PORT="${PORT:-8000}"

python -m uvicorn main:app --host 127.0.0.1 --port "$PORT" &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; }
trap cleanup EXIT

ok=0
for _ in $(seq 1 40); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/health')" 2>/dev/null; then
    ok=1
    break
  fi
  sleep 0.25
done

if [ "$ok" -ne 1 ]; then
  echo "Server did not become healthy on port ${PORT}."
  exit 1
fi

open "http://127.0.0.1:${PORT}/operator/"
wait "$PID"
