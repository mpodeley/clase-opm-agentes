# clase-opm-agentes

Class of 3 h 45 min for reservoir engineers: an introduction to driving a numerical simulator
(OPM Flow) with a coding agent (Claude Code). The exercise fits the Leverett J function that
initializes water saturation in the Hugin of Volve, using only the five wells logged before
first oil (12 February 2008). Two control wells are never shown to a case: 15/9-F-5 (logged July
2008, 5% of final oil produced, unswept) and 15/9-F-11 B (logged 2013, 77% produced, swept).
It ends with an autoresearch-style loop where each experiment is a hypothesis written in the
commit before the run, and a check of the tilted-contact hypothesis. Demo format: everything
runs on the instructor's machine.

## Layout

- `sw/` — the fixed pipeline. `pozo.py` (seven wells, Hugin only, net flag; LAS, DLIS and
  picks-based paths), `modelo.py` (case -> deck split into `SW.DATA`, `MODELO_*.INC` and the five
  `AJUSTE_*.INC`), `correr.py` (Flow in a container pinned by digest), `leer.py`, `puntaje.py`
  (the metric), `graficar.py` (one track per well on a common depth scale plus the J cloud).
- `evaluar.py` — the harness: `uv run evaluar.py [--caso F] [--etiqueta N] [--fragmento] [--experimento]`.
- `caso.py` — base case (untuned J1); the only file the agent edits in class.
- `program.md` — the loop instructions. `bitacora.py` — logbook, animation frames and GIF.
- `ejercicio/` — what the agent sees in class: its `CLAUDE.md`, `PEDIDO-1..4.md`, permissions.
  `ejercicio/preparar.sh` builds the working folder outside this repo (default `~/sw-volve`).
- `docente/` — never copied to the working folder: `soluciones/` (J1, J2, OP, T, P),
  `optimizar.py` (Nelder-Mead baseline), `tabla.py`, `barridos.py` (tilt and perched-water scans), `hipotesis.py` (rehearsal -> slides, page,
  animation), `guion.md`, `plan-b/` (reference runs, tilt scan, the rehearsed loop).
- `instalacion/` — `instalar.sh`, `verificar.sh`, the SPE1 deck.
- `slides/clase.md` — Marp deck, `podeley` theme in `slides/themes/`; `slides/build.sh`.
- `web/` — the public page: `index.html` and `contexto.py` (maps, sections, quick looks, Buckles,
  pressures, J review, tilt and perched-water scans) and `cubeta.py` (basin analysis of the base Hugin). `tools/publicar.sh [--cloudflare|--local]` builds `dist/`.
- `datos/preparar_datos.py` — 27 pinned files into `datos/volve/` (gitignored, 53 MB).

## Rules

1. The metric (`sw/puntaje.py`), the cell construction (`sw/pozo.py`) and the fluids in
   `sw/modelo.py` are frozen once the class is rehearsed: every number in `docente/guion.md`, the
   README, the deck and the page depends on them. After changing any, rerun `docente/tabla.py`,
   the tilt scan and the loop rehearsal, then update those four.
2. Reference cases keep the protocol `PARAMS` + `build(cells, p=PARAMS)` so `optimizar.py` can fit them.
3. `ejercicio/CLAUDE.md` must not leak answers: no fitted parameters, no fitted contact.
4. Prose in Spanish (README, deck, guion, page): load the `estilo` skill, profile `didactico`.
   Identifiers and comments in English.
5. The hypothesis slides, the page table and the animation are generated from
   `docente/plan-b/ensayo/` by `docente/hipotesis.py`; do not edit them by hand between the markers.
6. Tests: `uv run pytest`. `tests/test_flow.py` needs the container.

## Facts worth not rediscovering

- Flow 2026.04: `JFUNC` belongs in GRID and requires `ENDSCALE` in RUNSPEC. With
  `Pc = J * ST * (phi/k)^0.5 * 0.318316` and ST = sigma*cos(theta), Flow's J is the J of the
  Statoil report (their equation 23). ST is fixed at 2, the report's value.
- EQUIL item 9 is set to 0 (cell centre); the default integrates within the cell and departs from
  the closed form by up to 0.07 in Sw next to the contact.
- F-12's KLOGH in the 2007 interpreted file is about 40 times lower than the operator's 2009
  revision (`geomod09/..._KLOGH_NEW.las`). The revision is used for F-12, F-4 and 19 BT2.
- The exploration wells (19 SR, 19 A, 19 BT2) have no survey in the public mirrors; their path is
  interpolated between formation picks. F-4 is DLIS only (`dlisio`).
- Statoil 3781-06 contradicts itself: table 11 gives Volve Swirr = 0.45 - 0.105 log k, figure 20.b
  labels 0.412 - 0.088 log k; the text's a = 2.222 does not follow from figure 5.b. Case OP
  follows table 11.
- The field deck (`VOLVE_2016.DATA`, OPM-adapted mirror) has 12 EQUIL regions, zero capillary
  pressure and SWL per cell. No SWATINIT, no JFUNC.
- No SP log is usable (oil-based mud). No formation pressures in F-12. No public surfaces below
  the base of the Hugin, no fault polygons.
- F-4 has mobile water at its base (Sw 0.34 at 3,020 m in 3-darcy rock). `web/cubeta.py` fills the
  mapped base of the Hugin like a terrain, with steep steps as sealing faults: the block dips into
  a fault under F-4 and closes a small basin (spill 3,016 m at 39 degrees, 3,024 m at 45, none at
  56). Case P (a second EQLNUM for F-4) fits its local level at 3,033 m; the field deck has a
  "purged water" region at 3,025 m.
- F-5 has oil down to 3,144 m (Sw 0.30 to 0.39 at 3,120 to 3,144 m): it rules out the report's
  FWL of 3,120 m and agrees with the fitted 3,146 to 3,150 m. Blind RMSE on F-5: J1 0.090,
  P 0.075, operator's model 0.302, tilted contact 0.236.
- Field cumulatives at the control dates (operator's monthly file): end of June 2008, 0.48 MSm3
  oil and 0.46 MSm3 injected (all by F-4, 830 m from F-5); end of May 2013, 7.75 MSm3 oil (77% of
  the final 10.04), 19.15 MSm3 injected, water cut 85%.
- Headless `claude -p` in an untrusted folder ignores the allow list of `.claude/settings.json`.
