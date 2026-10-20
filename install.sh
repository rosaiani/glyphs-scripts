#!/bin/bash
# Installs the Plau scripts into the Glyphs 4 Scripts folder.
# Backs up the existing Plau folder first. Skips "(autosave)" copies, __pycache__ and .DS_Store.
# Nothing is deleted from the destination (e.g. scripts that only exist there are kept).
# Usage: ./install.sh

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)/Plau"
DEST="$HOME/Library/Application Support/Glyphs 4/Scripts/Plau"
BACKUP="$HOME/Library/Application Support/Glyphs 4/Scripts-backups/Plau-$(date +%Y%m%d-%H%M%S)"

if [ ! -d "$SRC" ]; then
  echo "Plau folder not found next to this script: $SRC" >&2
  exit 1
fi

mkdir -p "$DEST"

if [ -n "$(ls -A "$DEST")" ]; then
  mkdir -p "$(dirname "$BACKUP")"
  cp -R "$DEST" "$BACKUP"
  echo "Backup: $BACKUP"
fi

rsync -av \
  --exclude='*(autosave).py' \
  --exclude='__pycache__' \
  --exclude='.DS_Store*' \
  "$SRC/" "$DEST/"

echo
echo "Done. In Glyphs, hold Option and choose Script > Reload Scripts (restart Glyphs if needed)."
