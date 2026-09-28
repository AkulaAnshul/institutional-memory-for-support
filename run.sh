#!/usr/bin/env bash
# Run the support console. Uses the project-local conda env; touches nothing global.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x ".conda/bin/python" ]; then
  echo "No ./.conda env found. Create it with:"
  echo "  conda create --prefix ./.conda python=3.11 -y"
  echo "  ./.conda/bin/pip install -r requirements.txt"
  exit 1
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
exec ./.conda/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"
