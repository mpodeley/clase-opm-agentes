#!/usr/bin/env bash
# Build the deck: figures from docente/plan-b/ into slides/img/, then Marp to slides/clase.html.
#
#   slides/build.sh          HTML
#   slides/build.sh --pdf    PDF with speaker notes (needs a Chromium; see MARP_BROWSER)
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"

if [ ! -f docente/plan-b/tabla.md ]; then
    uv run docente/tabla.py
fi
mkdir -p slides/img
for c in a b e f1 f2; do
    cp "docente/plan-b/$c/perfil.png" "slides/img/caso-$c.png"
done
uv run python -c "
from pathlib import Path
from sw import graficar, pozo
graficar.log_only(pozo.load_all(), 'F-12', Path('slides/img/perfil-f12.png'))
"

marp="${MARP:-}"
if [ -z "$marp" ]; then
    if command -v marp >/dev/null; then marp=marp
    else marp="npx --yes @marp-team/marp-cli"
    fi
fi

if [ "${1:-}" = "--pdf" ]; then
    $marp --no-stdin --theme-set slides/themes --allow-local-files --pdf --pdf-notes slides/clase.md -o slides/clase.pdf
else
    $marp --no-stdin --theme-set slides/themes --html slides/clase.md -o slides/clase.html
fi
