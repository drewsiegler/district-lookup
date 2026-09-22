#!/bin/bash
# Double-click this file in Finder to open District Lookup in your browser.
# Leave the Terminal window it opens running; closing it stops the app.
cd "$(dirname "$0")" || exit 1

if [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
elif command -v python3 > /dev/null; then
  PYTHON=python3
  echo "No .venv found here — using system python3."
  echo "If this fails, see the Setup section of README.md."
  echo
else
  echo "Python 3 isn't installed. See the Setup section of README.md."
  read -r -p "Press Return to close."
  exit 1
fi

"$PYTHON" src/web.py
echo
read -r -p "District Lookup has stopped. Press Return to close this window."
