#!/usr/bin/env bash
# One-command setup. Creates a project-local Python env and installs dependencies.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Setting up the Institutional Memory console"

if [ -x ".conda/bin/python" ]; then
  echo "Local conda environment already exists."
elif command -v conda >/dev/null 2>&1; then
  echo "Creating a local conda environment (./.conda) ..."
  conda create --prefix ./.conda python=3.11 -y
elif command -v python3 >/dev/null 2>&1; then
  echo "conda not found; creating a local virtual environment (./.venv) ..."
  python3 -m venv .venv
else
  echo "Python 3.11+ is required but was not found. Install Anaconda or Python, then re-run."
  exit 1
fi

if [ -x ".conda/bin/python" ]; then
  PY=".conda/bin/python"; PIP=".conda/bin/pip"
else
  PY=".venv/bin/python"; PIP=".venv/bin/pip"
fi

echo "Installing Python packages (this can take a minute) ..."
"$PIP" install -q --upgrade pip
"$PIP" install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "A .env file was created. Open it and paste your GROQ_API_KEY and HINDSIGHT_API_KEY."
fi

echo
echo "Setup complete."
echo "Start the console with:   ./run.sh"
