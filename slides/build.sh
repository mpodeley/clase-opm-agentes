#!/usr/bin/env bash
# Build the deck: figures into slides/img/, then Marp to slides/clase.html.
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
for c in base j1 op j2 t p; do
    cp "docente/plan-b/$c/perfil.png" "slides/img/caso-$c.png"
done
cp slides/static/*.svg slides/img/
uv run web/contexto.py slides/img > /dev/null
uv run web/cubeta.py slides/img > /dev/null
uv run docente/hipotesis.py
# The loop rehearsal as an animation: one frame per experiment (made by hipotesis.py).
mkdir -p slides/img/loop
rm -f slides/img/loop/*.png
cp docente/plan-b/ensayo/corridas/animacion/*.png slides/img/loop/
cp docente/plan-b/ensayo/animacion.gif slides/img/loop.gif

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
