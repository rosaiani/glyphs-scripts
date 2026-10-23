#!/bin/bash
# Runs "Windows Font Fix.py" with a Python that has fontTools, for use as a Glyphs Post-Export Command.
# Glyphs starts commands without your shell environment, so look for Python in the usual places.
# Usage: windows-font-fix.sh exported-font.ttf [options]

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$DIR/Windows Font Fix.py"

candidates=()
for p in "$HOME"/.pyenv/versions/*/bin/python3; do
  [ -x "$p" ] && candidates+=("$p")
done
candidates+=(
  /opt/homebrew/bin/python3
  /usr/local/bin/python3
  /Library/Frameworks/Python.framework/Versions/Current/bin/python3
  /usr/bin/python3
)

for py in "${candidates[@]}"; do
  if [ -x "$py" ] && "$py" -c "import fontTools" 2>/dev/null; then
    exec "$py" "$SCRIPT" "$@"
  fi
done

echo "Windows Font Fix: no Python with fontTools found. Install it with: pip3 install fonttools" >&2
exit 1
