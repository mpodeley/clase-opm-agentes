"""From a fitting case to an OPM Flow deck that only initializes.

The deck is a row of cells (NX = number of cells, NY = NZ = 1), each with its own top depth.
Transmissibility between neighbours is zero, so nothing flows: the simulator is used for its
equilibration, which is the calculation a full-field model will repeat with these same keywords.

The deck is split so that the fit is visible. SW.DATA is the skeleton, MODELO_*.INC hold the
grid, the rock and the fluids, which never change, and AJUSTE_*.INC hold what a case decides:

    AJUSTE_GRID.INC       JFUNC
    AJUSTE_PROPS.INC      SWOF: the J (or Pc) table of each saturation region
    AJUSTE_SWL.INC        SWL per cell, when the case scales connate water
    AJUSTE_REGIONES.INC   SATNUM and EQLNUM per cell
    AJUSTE_SOLUTION.INC   EQUIL: one free water level per equilibration region
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from sw.pozo import Cells

DECK_NAME = 'SW'
MAX_PARAMETERS = 6

# Reservoir fluid densities the operator used for saturation-height (Statoil doc. 3781-06,
# section 6, from DST analysis). The 2008 lab report on the F-4 oil gives 720.5 kg/m3 at
# bubble point, in line with the first.
OIL_DENSITY = 720.0       # kg/m3
WATER_DENSITY = 1065.0    # kg/m3
DATUM_PRESSURE = 330.0    # bar at the free water level; initialization does not depend on it
GRAVITY_BAR_PER_M = (WATER_DENSITY - OIL_DENSITY) * 9.80665 / 1e5   # bar per metre above the FWL
# Flow, metric units: Pc[bar] = J * tension[dyn/cm] * (phi/k[mD])**0.5 * 0.318316. With the
# tension set to sigma*cos(theta), that is the J of the Statoil report (their equation 23).
JFUNC_METRIC_CONSTANT = 0.318316
SIGMA_COS_THETA = 2.0     # mN/m, the value in table 11 of the report; fixed, so that J is comparable

J_TABLE_MAX = 1e5

FIT_FILES = ('AJUSTE_GRID.INC', 'AJUSTE_PROPS.INC', 'AJUSTE_SWL.INC', 'AJUSTE_REGIONES.INC',
             'AJUSTE_SOLUTION.INC')


@dataclass(frozen=True)
class PcCurve:
    """Drainage curve as a table. `pc` is the dimensionless J with JFUNC, or bar without it."""
    sw: np.ndarray
    pc: np.ndarray


def brooks_corey(swirr: float, pe: float, lam: float, n: int = 30) -> PcCurve:
    """J = pe * Sw*^(-1/lam), with Sw* = (Sw - swirr) / (1 - swirr).

    `pe` is the entry value (J at Sw = 1) and `lam` the pore size distribution index: a large
    `lam` gives a short transition zone. In the notation of the Statoil report,
    Swn = a * J^-b with b = lam and a = pe^lam.
    """
    if not (0.0 <= swirr < 1.0 and pe > 0.0 and lam > 0.0):
        raise ValueError(f'brooks_corey: parámetros fuera de rango (swirr={swirr}, pe={pe}, lam={lam})')
    # The table stops where J reaches J_TABLE_MAX: far beyond any cell, and it keeps the numbers readable.
    s = np.geomspace(max(1e-3, (J_TABLE_MAX / pe) ** (-lam)), 1.0, n)
    return PcCurve(sw=swirr + s * (1.0 - swirr), pc=pe * s ** (-1.0 / lam))


@dataclass(frozen=True)
class JFunction:
    """Leverett scaling: Pc = J(Sw) * tension * (phi/k)^alpha (Flow keyword JFUNC)."""
    surface_tension: float = SIGMA_COS_THETA   # dyn/cm
    alpha: float = 0.5                         # exponent of porosity
    beta: float = 0.5                          # exponent of permeability


@dataclass
class Case:
    """One way of initializing water saturation. Arrays have one entry per cell."""
    description: str
    curves: list[PcCurve]                 # one per saturation region
    fwl: list[float]                      # free water level per equilibration region, m TVDSS
    n_parameters: int                     # how many numbers were tuned to get here
    satnum: np.ndarray | None = None      # 1-based curve per cell; default: all 1
    eqlnum: np.ndarray | None = None      # 1-based FWL per cell; default: all 1
    jfunc: JFunction | None = None
    swl: np.ndarray | None = None         # connate water per cell (end-point scaling)

    def resolved(self, n: int) -> 'Case':
        """Fill defaults and check shapes and ranges. Raises ValueError with a message for the log."""
        if not 0 <= int(self.n_parameters) <= MAX_PARAMETERS:
            raise ValueError(f'n_parameters = {self.n_parameters}: el máximo es {MAX_PARAMETERS}')
        satnum = np.ones(n, dtype=int) if self.satnum is None else np.asarray(self.satnum, dtype=int)
        eqlnum = np.ones(n, dtype=int) if self.eqlnum is None else np.asarray(self.eqlnum, dtype=int)
        for name, arr, count in (('satnum', satnum, len(self.curves)), ('eqlnum', eqlnum, len(self.fwl))):
            if arr.shape != (n,):
                raise ValueError(f'{name}: se esperaban {n} valores, hay {arr.shape}')
            if arr.min() < 1 or arr.max() > count:
                raise ValueError(f'{name}: valores entre {arr.min()} y {arr.max()}, pero hay {count} tablas')
        swl = None
        if self.swl is not None:
            swl = np.asarray(self.swl, dtype=float)
            if swl.shape != (n,):
                raise ValueError(f'swl: se esperaban {n} valores, hay {swl.shape}')
            if not np.all(np.isfinite(swl)) or swl.min() < 0.0 or swl.max() >= 1.0:
                raise ValueError('swl: valores fuera de [0, 1)')
        for i, c in enumerate(self.curves, 1):
            if len(c.sw) < 2 or np.any(np.diff(c.sw) <= 0) or np.any(np.diff(c.pc) > 0):
                raise ValueError(f'curva {i}: Sw debe crecer y J no puede crecer con Sw')
            if c.sw[-1] != 1.0 or c.sw[0] < 0.0 or c.pc[-1] < 0.0:
                raise ValueError(f'curva {i}: la tabla debe terminar en Sw = 1 con J >= 0')
        return Case(self.description, self.curves, [float(f) for f in self.fwl], int(self.n_parameters),
                    satnum, eqlnum, self.jfunc, swl)


def _array(keyword: str, values: np.ndarray, fmt: str, per_line: int = 8) -> str:
    items = [format(v, fmt) for v in values]
    lines = [' ' + ' '.join(items[i:i + per_line]) for i in range(0, len(items), per_line)]
    return f'{keyword}\n' + '\n'.join(lines) + ' /\n'


def _swof(curve: PcCurve) -> str:
    """SWOF table. Relative permeabilities are plain Corey curves: initialization ignores them."""
    s = (curve.sw - curve.sw[0]) / (1.0 - curve.sw[0])
    rows = [f' {sw:.6f} {krw:.6f} {kro:.6f} {pc:.6g}'
            for sw, krw, kro, pc in zip(curve.sw, s ** 3, (1.0 - s) ** 2, curve.pc)]
    return '\n'.join(rows) + ' /\n'


def deck_files(case: Case, cells: Cells) -> dict[str, str]:
    """Every file of the deck, by name."""
    n = len(cells)
    case = case.resolved(n)
    endscale = case.swl is not None or case.jfunc is not None   # Flow requires ENDSCALE with JFUNC
    nrows = max(len(c.sw) for c in case.curves)
    unit = 'J, adimensional' if case.jfunc else 'Pc, bar'

    skeleton = ['-- Generated by sw/modelo.py. Do not edit: change caso.py and run evaluar.py.',
                f'-- {case.description}', 'RUNSPEC', 'TITLE', f' {case.description[:70]}',
                'DIMENS', f' {n} 1 1 /', 'OIL', 'WATER', 'METRIC',
                'TABDIMS', f' {len(case.curves)} 1 {nrows} 20 /',
                'EQLDIMS', f' {len(case.fwl)} /']
    if endscale:
        skeleton += ['ENDSCALE', '/']
    skeleton += ['START', " 31 'DEC' 2007 /", 'UNIFOUT', '',
                 'GRID', 'INIT',
                 'INCLUDE', " 'AJUSTE_GRID.INC' /", 'INCLUDE', " 'MODELO_GRID.INC' /", '',
                 'PROPS',
                 'INCLUDE', " 'MODELO_PROPS.INC' /", 'INCLUDE', " 'AJUSTE_PROPS.INC' /",
                 'INCLUDE', " 'AJUSTE_SWL.INC' /", '',
                 'REGIONS', 'INCLUDE', " 'AJUSTE_REGIONES.INC' /", '',
                 'SOLUTION', 'INCLUDE', " 'AJUSTE_SOLUTION.INC' /",
                 'RPTRST', ' BASIC=2 /', '', 'SUMMARY', 'FOIP', '', 'SCHEDULE', 'TSTEP', ' 0.001 /', 'END', '']

    grid = '-- One cell per metre of hole, in the order of sw/pozo.py. Fixed.\n'
    grid += f'DX\n {n}*1 /\nDY\n {n}*1 /\n'
    grid += _array('DZ', cells.dz, '.4f')
    grid += _array('TOPS', cells.tvdss - 0.5 * cells.dz, '.3f')
    grid += _array('PORO', cells.phi, '.5f')
    grid += _array('PERMX', cells.k, '.6g')
    grid += 'COPY\n PERMX PERMY /\n PERMX PERMZ /\n/\n'
    grid += f'-- No flow between cells: each one equilibrates on its own.\nMULTX\n {n}*0 /\n'

    props = '-- Fluids and rock. Fixed: densities from Statoil doc. 3781-06, section 6.\n'
    props += 'ROCK\n 330 4E-5 /\n'
    props += 'PVDO\n 100 1.0002 1.0\n 600 1.0000 1.0 /\n'
    props += 'PVTW\n 330 1.0 4E-5 0.4 0 /\n'
    props += f'DENSITY\n {OIL_DENSITY:g} {WATER_DENSITY:g} 1 /\n'

    if case.jfunc is None:
        fit_grid = '-- Sin función J: la columna de presión capilar de SWOF está en bar.\n'
    else:
        j = case.jfunc
        fit_grid = ('-- Escalado de Leverett: Pc = J(Sw) * tension * (PORO/PERMX)^0.5\n'
                    '--     fase  tension(dyn/cm)  gas  alpha(phi)  beta(k)  dirección\n'
                    f'JFUNC\n WATER {j.surface_tension:g} 1* {j.alpha:g} {j.beta:g} XY /\n')

    fit_props = f'-- Una tabla por región de saturación (SATNUM).\n--   Sw        krw      kro      {unit}\nSWOF\n'
    fit_props += ''.join(_swof(c) for c in case.curves)

    if case.swl is None:
        fit_swl = '-- Sin escalado de extremos: el agua irreducible es la de la tabla.\n'
    else:
        fit_swl = '-- Agua connata por celda: la tabla de SWOF se reescala entre SWL y 1.\n'
        fit_swl += _array('SWL', case.swl, '.5f') + _array('SWCR', case.swl, '.5f')

    fit_regions = '-- Qué tabla (SATNUM) y qué contacto (EQLNUM) le toca a cada celda.\n'
    fit_regions += _array('SATNUM', case.satnum, 'd', per_line=20)
    fit_regions += _array('EQLNUM', case.eqlnum, 'd', per_line=20)

    fit_solution = ('-- Un registro por región de equilibrio. Datum y contacto en el nivel de agua libre (FWL).\n'
                    '--  datum(m)  presión(bar)  contacto(m)  Pc en el contacto  ...  0 = equilibrio al centro de la celda\nEQUIL\n')
    for fwl in case.fwl:
        fit_solution += f' {fwl:.3f} {DATUM_PRESSURE:g} {fwl:.3f} 0 1* 1* 1* 1* 0 /\n'

    return {f'{DECK_NAME}.DATA': '\n'.join(skeleton), 'MODELO_GRID.INC': grid, 'MODELO_PROPS.INC': props,
            'AJUSTE_GRID.INC': fit_grid, 'AJUSTE_PROPS.INC': fit_props, 'AJUSTE_SWL.INC': fit_swl,
            'AJUSTE_REGIONES.INC': fit_regions, 'AJUSTE_SOLUTION.INC': fit_solution}


def write_deck(case: Case, cells: Cells, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in deck_files(case, cells).items():
        (directory / name).write_text(text)
    return directory / f'{DECK_NAME}.DATA'


def fragment(directory: Path, max_rows: int = 6) -> str:
    """The part of the deck a case decides, short enough to read on a slide.

    Tables are cut to their first and last rows and per-cell arrays to a one-line summary.
    """
    out = []
    for name in FIT_FILES:
        lines = (directory / name).read_text().splitlines()
        out.append(f'-- ===== {name}')
        if name in ('AJUSTE_SWL.INC', 'AJUSTE_REGIONES.INC'):
            out.append(lines[0])
            keyword, values = None, []
            for line in lines[1:] + ['END']:
                if line and not line.startswith(' '):
                    if keyword and keyword != 'SWCR':
                        v = np.array(values, dtype=float)
                        kinds = np.unique(v)
                        detail = (', '.join(f'{int(u)}: {int((v == u).sum())} celdas' for u in kinds)
                                  if len(kinds) <= 8 else f'de {v.min():.3f} a {v.max():.3f}')
                        out.append(f'{keyword}   -- {len(v)} valores, {detail}')
                    keyword, values = line.strip(), []
                else:
                    values += line.replace('/', ' ').split()
            continue
        table = []
        for line in lines:
            if line.startswith(' ') and len(line.split()) == 4 and not line.rstrip().endswith('/'):
                table.append(line)
                continue
            if len(table) > max_rows:
                table = table[:max_rows - 2] + [f'   ...  ({len(table) - max_rows + 2} filas más)'] + table[-2:]
            out += table + [line]
            table = []
    return '\n'.join(out)
