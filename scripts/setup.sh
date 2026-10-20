#!/usr/bin/env bash
# Create .venv with Python 3.12 or newer and install the project with its test dependencies.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=""
for candidate in python3.14 python3.13 python3.12 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 12))' 2>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Python 3.12 or newer is required. Install it, then run this script again." >&2
  exit 1
fi

echo "Using $("$PYTHON" --version)"
"$PYTHON" -m venv .venv
VENV_PYTHON=.venv/bin/python
[ -x .venv/Scripts/python.exe ] && VENV_PYTHON=.venv/Scripts/python.exe  # Git Bash on Windows
"$VENV_PYTHON" -m pip install -e ".[dev]"
echo "Setup done. Next: scripts/test.sh, scripts/demo.sh or scripts/run.sh"
