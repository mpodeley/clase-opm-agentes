#!/usr/bin/env bash
# Install what the class needs: the OPM Flow image, the Python environment and the Volve files.
#
#   instalacion/instalar.sh            podman (default)
#   CONTENEDOR=docker instalacion/instalar.sh
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
runtime="${CONTENEDOR:-podman}"
image="docker.io/openporousmedia/opmreleases@sha256:db8865d7c80440513c8c73df7ed385a3b7d2e055a0ef95f7662ec06ef6a6b3a9"

for tool in "$runtime" uv git; do
    if ! command -v "$tool" >/dev/null; then
        echo "falta $tool: ver README.md, sección Instalación" >&2
        exit 1
    fi
done

echo "1/3  imagen de OPM Flow 2026.04 (1.2 GB la primera vez)"
"$runtime" image exists "$image" 2>/dev/null || "$runtime" pull "$image"

echo "2/3  entorno de Python"
cd "$repo"
uv sync --quiet

echo "3/3  datos de Volve"
uv run datos/preparar_datos.py

echo "listo: probar con instalacion/verificar.sh"
