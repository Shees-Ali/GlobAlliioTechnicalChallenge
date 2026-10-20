#!/usr/bin/env bash
# Start the app, then open http://127.0.0.1:8000/demo. Extra arguments go to uvicorn, for example: --port 8001
set -euo pipefail
cd "$(dirname "$0")/.."

VENV_PYTHON=.venv/bin/python
[ -x .venv/Scripts/python.exe ] && VENV_PYTHON=.venv/Scripts/python.exe  # Git Bash on Windows
if [ ! -e "$VENV_PYTHON" ]; then
  echo "No .venv found. Run scripts/setup.sh first." >&2
  exit 1
fi
exec "$VENV_PYTHON" -m uvicorn notifications.api.app:app "$@"
