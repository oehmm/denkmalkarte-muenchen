#!/bin/sh
# Baut die Handy-Version neu und veröffentlicht sie über GitHub Pages (Ordner docs/).
set -e
cd "$(dirname "$0")/.."
python3 scripts/assemble.py
git add -A
git commit -m "Denkmalkarte aktualisieren" || echo "Keine Änderungen."
git push
echo "Live in 1–2 Minuten: https://oehmm.github.io/denkmalkarte-muenchen/"
