#!/usr/bin/env bash
# Build the folder the agent works in during the class, outside this repo, so that it reads
# the exercise CLAUDE.md and never sees docente/ (the reference cases).
#
#   ejercicio/preparar.sh [destino]     default: ~/sw-volve
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
dest="${1:-$HOME/sw-volve}"

if [ -e "$dest" ]; then
    echo "ya existe $dest: borrarlo o elegir otro destino" >&2
    exit 1
fi
if [ ! -d "$repo/datos/volve" ]; then
    echo "faltan los datos: correr primero  uv run datos/preparar_datos.py" >&2
    exit 1
fi

mkdir -p "$dest/casos" "$dest/datos" "$dest/.claude"
cp -r "$repo/sw" "$dest/sw"
cp -r "$repo/datos/volve" "$dest/datos/volve"
cp "$repo/evaluar.py" "$repo/bitacora.py" "$repo/caso.py" "$repo/program.md" "$repo/pyproject.toml" "$repo/uv.lock" "$dest/"
cp "$repo/caso.py" "$dest/casos/base.py"
cp "$repo/ejercicio/CLAUDE.md" "$repo"/ejercicio/PEDIDO-*.md "$dest/"
cp "$repo/ejercicio/.claude/settings.json" "$dest/.claude/"
find "$dest/sw" -name __pycache__ -prune -exec rm -r {} +
printf '%s\n' '.venv/' '__pycache__/' 'corridas/' 'run.log' 'results.tsv' 'bitacora.html' > "$dest/.gitignore"

cd "$dest"
uv sync --quiet --no-dev
git init -q -b main
git add -A
git -c user.name="clase" -c user.email="clase@localhost" commit -q -m "caso base"
uv run evaluar.py --sin-grafico | grep -E "^(caso|rmse_ajuste|rmse_control):"
echo "listo: cd $dest && claude"
