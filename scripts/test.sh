#!/usr/bin/env bash
# Run the test suite. Extra arguments go to pytest, for example: scripts/test.sh -q
set -euo pipefail
cd "$(dirname "$0")/.."

VENV_PYTHON=.venv/bin/python
[ -x .venv/Scripts/python.exe ] && VENV_PYTHON=.venv/Scripts/python.exe  # Git Bash on Windows
if [ ! -e "$VENV_PYTHON" ]; then
  echo "No .venv found. Run scripts/setup.sh first." >&2
  exit 1
fi
exec "$VENV_PYTHON" -m pytest "$@"
