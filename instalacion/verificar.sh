#!/usr/bin/env bash
# Check the installation end to end: Flow answers, SPE1 runs, the base case scores.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
runtime="${CONTENEDOR:-podman}"
image="docker.io/openporousmedia/opmreleases@sha256:db8865d7c80440513c8c73df7ed385a3b7d2e055a0ef95f7662ec06ef6a6b3a9"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "1/3  versión de Flow"
"$runtime" run --rm --pull=never --network=none --entrypoint=flow "$image" --version

echo "2/3  SPE1: primer caso comparativo de la SPE, 10 años de inyección de gas"
mkdir -p "$work/in" "$work/out"
cp "$repo/instalacion/SPE1CASE1.DATA" "$work/in/"
userns=()
[ "$runtime" = podman ] && userns=(--userns=keep-id)
start=$(date +%s.%N)
"$runtime" run --rm --pull=never --network=none "${userns[@]}" --user "$(id -u):$(id -g)" \
    -v "$work/in:/input:ro,Z" -v "$work/out:/output:Z" -w /input --entrypoint=flow "$image" \
    /input/SPE1CASE1.DATA --output-dir=/output > "$work/spe1.log" 2>&1 \
    || { tail -n 20 "$work/spe1.log"; exit 1; }
grep -q "End of simulation" "$work/spe1.log"
printf '     terminó en %.1f s\n' "$(echo "$(date +%s.%N) - $start" | bc)"

echo "3/3  caso base del ejercicio"
cd "$repo"
uv run evaluar.py --sin-grafico --salida "$work/base" | grep -E "^(caso|rmse_ajuste|segundos_flow):"

echo "todo en orden"
