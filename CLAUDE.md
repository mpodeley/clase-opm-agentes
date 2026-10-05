# clase-opm-agentes

Class of up to 4 hours for reservoir engineers: an introduction to driving a numerical simulator
(OPM Flow) with a coding agent (Claude Code). The exercise fits the initial water saturation of a
model to the interpreted logs of two Volve wells, comparing alternatives (single curve, Leverett J,
rock types, end-point scaling, SWATINIT, flat or tilted contact), and ends with an
autoresearch-style loop. Demo format: everything runs on the instructor's machine.

## Layout

- `sw/` — the fixed pipeline. `pozo.py` (LAS + trajectory -> cells), `modelo.py` (case -> deck),
  `correr.py` (Flow in a container pinned by digest), `leer.py` (initial SWAT), `puntaje.py`
  (the metric), `graficar.py` (the figure).
- `evaluar.py` — the harness: `uv run evaluar.py [--caso F] [--salida D] [--ver-validacion]`.
- `caso.py` — base case; the only file the agent edits in class.
- `program.md` — the loop instructions (adapted from karpathy/autoresearch).
- `ejercicio/` — what the agent sees in class: its `CLAUDE.md`, `PEDIDO-1..4.md`, permissions.
  `ejercicio/preparar.sh` builds the working folder outside this repo (default `~/sw-volve`).
- `docente/` — never copied to the working folder: `soluciones/` (reference cases A–F2),
  `optimizar.py` (Nelder-Mead baseline), `guion.md` (timing), `plan-b/` (recorded outputs).
- `instalacion/` — `instalar.sh`, `verificar.sh`, the SPE1 deck.
- `slides/clase.md` — Marp deck, `podeley` theme in `slides/themes/`.
- `datos/preparar_datos.py` — pinned mirrors of the Volve files into `datos/volve/` (gitignored).

## Rules

1. The metric (`sw/puntaje.py`) and the cell construction (`sw/pozo.py`) are frozen once the class
   is rehearsed: every number in `docente/guion.md`, the README and the deck depends on them.
   After changing either, rerun `docente/tabla.py` and update those three.
2. Reference cases keep the protocol `PARAMS` + `build(cells, p=PARAMS)` so `optimizar.py` can fit them.
3. `ejercicio/CLAUDE.md` must not leak answers: no fitted parameters, no contact depths.
4. Prose in Spanish (README, deck, guion): load the `estilo` skill, profile `didactico`.
   Identifiers and comments in English.
5. Tests: `uv run pytest`. `tests/test_flow.py` needs the container; it checks Flow against the
   closed-form saturation-height function.

## Facts worth not rediscovering

- Flow 2026.04: `JFUNC` belongs in GRID and requires `ENDSCALE` in RUNSPEC.
- `SWATINIT` is ignored below the free water level (Sw = 1 there).
- F-12 was logged in 2007, before first oil (February 2008). F-11 B was logged in 2013, after five
  years of production and water injection: its Sw is not an initial state.
- The data set has no formation pressures, no SCAL and no PVT. Fluid densities in `sw/modelo.py`
  are an assumption.
