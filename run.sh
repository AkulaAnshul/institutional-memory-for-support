#!/usr/bin/env bash
# Run the support console.
#
# Prefers a project-local conda env, then a project-local venv, then system python3.
# Nothing global is modified.
set -euo pipefail
cd "$(dirname "$0")"

if [ -x ".conda/bin/python" ]; then
  PY=".conda/bin/python"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "No Python found. Create an environment first, e.g.:"
  echo "  conda create --prefix ./.conda python=3.11 -y && ./.conda/bin/pip install -r requirements.txt"
  echo "  # or"
  echo "  python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
echo "Starting on http://${HOST}:${PORT} using ${PY}"
exec "$PY" -m uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"
