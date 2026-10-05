"""From a fitting case to an OPM Flow deck that only initializes.

The deck is a row of cells (NX = number of cells, NY = NZ = 1), each with its own top depth.
Transmissibility between neighbours is zero, so nothing flows: the simulator is used for its
equilibration, which is the calculation a full-field model will repeat with these same keywords.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from sw.pozo import Cells

DECK_NAME = 'SW'

# Fluids are fixed for every case: there is no PVT report in the data set.
OIL_DENSITY = 750.0       # kg/m3 at reservoir conditions (Bo taken as 1)
WATER_DENSITY = 1040.0    # kg/m3
DATUM_PRESSURE = 330.0    # bar at the free water level
GRAVITY_BAR_PER_M = (WATER_DENSITY - OIL_DENSITY) * 9.80665 / 1e5   # bar per metre above the FWL
JFUNC_METRIC_CONSTANT = 0.318316   # Pc[bar] = J * tension[dyn/cm] * (phi/k[mD])**0.5 * constant


@dataclass(frozen=True)
class PcCurve:
    """Drainage curve as a table. `pc` is in bar, or the dimensionless J when the case uses JFUNC."""
    sw: np.ndarray
    pc: np.ndarray


def brooks_corey(swirr: float, pe: float, lam: float, n: int = 30) -> PcCurve:
    """Pc = pe * Sw*^(-1/lam), with Sw* = (Sw - swirr) / (1 - swirr).

    `pe` is the entry pressure (bar, or entry J with JFUNC) and `lam` the pore size
    distribution index: a large `lam` gives a short transition zone.
    """
    if not (0.0 <= swirr < 1.0 and pe > 0.0 and lam > 0.0):
        raise ValueError(f'brooks_corey: parámetros fuera de rango (swirr={swirr}, pe={pe}, lam={lam})')
    s = np.geomspace(1e-3, 1.0, n)
    return PcCurve(sw=swirr + s * (1.0 - swirr), pc=pe * s ** (-1.0 / lam))


@dataclass(frozen=True)
class JFunction:
    """Leverett scaling: Pc = J(Sw) * tension * (phi/k)^alpha (Flow keyword JFUNC)."""
    surface_tension: float = 30.0   # dyn/cm
    alpha: float = 0.5              # exponent of porosity
    beta: float = 0.5               # exponent of permeability


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
    swatinit: np.ndarray | None = None    # target Sw per cell; NaN = let equilibration decide
    ppcwmax: float | None = None          # cap on the scaled Pc when swatinit is used, bar

    def resolved(self, n: int) -> 'Case':
        """Fill defaults and check shapes and ranges. Raises ValueError with a message for the log."""
        satnum = np.ones(n, dtype=int) if self.satnum is None else np.asarray(self.satnum, dtype=int)
        eqlnum = np.ones(n, dtype=int) if self.eqlnum is None else np.asarray(self.eqlnum, dtype=int)
        for name, arr, count in (('satnum', satnum, len(self.curves)), ('eqlnum', eqlnum, len(self.fwl))):
            if arr.shape != (n,):
                raise ValueError(f'{name}: se esperaban {n} valores, hay {arr.shape}')
            if arr.min() < 1 or arr.max() > count:
                raise ValueError(f'{name}: valores entre {arr.min()} y {arr.max()}, pero hay {count} tablas')
        for name, arr in (('swl', self.swl), ('swatinit', self.swatinit)):
            if arr is None:
                continue
            arr = np.asarray(arr, dtype=float)
            if arr.shape != (n,):
                raise ValueError(f'{name}: se esperaban {n} valores, hay {arr.shape}')
            if np.nanmin(arr) < 0.0 or np.nanmax(arr) > 1.0:
                raise ValueError(f'{name}: valores fuera de [0, 1]')
        if self.swl is not None and not np.all(np.isfinite(self.swl)):
            raise ValueError('swl: hay valores no finitos')
        for i, c in enumerate(self.curves, 1):
            if len(c.sw) < 2 or np.any(np.diff(c.sw) <= 0) or np.any(np.diff(c.pc) > 0):
                raise ValueError(f'curva {i}: Sw debe crecer y Pc no puede crecer con Sw')
            if c.sw[-1] != 1.0 or c.sw[0] < 0.0 or c.pc[-1] < 0.0:
                raise ValueError(f'curva {i}: la tabla debe terminar en Sw = 1 con Pc >= 0')
        if self.swatinit is not None and self.jfunc is not None:
            raise ValueError('swatinit y jfunc no se combinan en esta clase: elegir uno')
        return Case(self.description, self.curves, [float(f) for f in self.fwl], int(self.n_parameters),
                    satnum, eqlnum, self.jfunc,
                    None if self.swl is None else np.asarray(self.swl, dtype=float),
                    None if self.swatinit is None else np.asarray(self.swatinit, dtype=float),
                    self.ppcwmax)


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


def deck_text(case: Case, cells: Cells) -> str:
    n = len(cells)
    case = case.resolved(n)
    if case.swatinit is not None and np.any(np.isnan(case.swatinit)):
        raise ValueError('swatinit con NaN: el arnés debe completarlo antes de escribir el deck')
    endscale = case.swl is not None or case.jfunc is not None   # Flow requires ENDSCALE with JFUNC
    nrows = max(len(c.sw) for c in case.curves)

    out = ['-- Generated by sw/modelo.py. Do not edit: change caso.py and run evaluar.py.',
           f'-- {case.description}', 'RUNSPEC', 'TITLE', f' {case.description[:70]}',
           'DIMENS', f' {n} 1 1 /', 'OIL', 'WATER', 'METRIC',
           'TABDIMS', f' {len(case.curves)} 1 {nrows} 20 /',
           'EQLDIMS', f' {len(case.fwl)} /']
    if endscale:
        out += ['ENDSCALE', '/']
    out += ['START', " 1 'JAN' 2008 /", 'UNIFOUT', '', 'GRID', 'INIT']
    if case.jfunc is not None:
        j = case.jfunc
        out += ['JFUNC', f' WATER {j.surface_tension:g} 1* {j.alpha:g} {j.beta:g} XY /']
    text = '\n'.join(out) + '\n'
    text += f'DX\n {n}*1 /\nDY\n {n}*1 /\n'
    text += _array('DZ', cells.dz, '.4f')
    text += _array('TOPS', cells.tvdss - 0.5 * cells.dz, '.3f')
    text += _array('PORO', cells.phi, '.5f')
    text += _array('PERMX', cells.k, '.6g')
    text += 'COPY\n PERMX PERMY /\n PERMX PERMZ /\n/\n'
    text += f'-- No flow between cells: each one equilibrates on its own.\nMULTX\n {n}*0 /\n'

    text += '\nPROPS\n'
    text += 'ROCK\n 330 4E-5 /\n'
    text += 'PVDO\n 100 1.0002 1.0\n 600 1.0000 1.0 /\n'
    text += 'PVTW\n 330 1.0 4E-5 0.4 0 /\n'
    text += f'DENSITY\n {OIL_DENSITY:g} {WATER_DENSITY:g} 1 /\n'
    text += 'SWOF\n' + ''.join(_swof(c) for c in case.curves)
    if case.swl is not None:
        text += _array('SWL', case.swl, '.5f')
        text += _array('SWCR', case.swl, '.5f')
    if case.swatinit is not None:
        text += _array('SWATINIT', case.swatinit, '.5f')
        if case.ppcwmax is not None:
            text += 'PPCWMAX\n' + f' {case.ppcwmax:g} NO /\n' * len(case.curves)

    text += '\nREGIONS\n'
    text += _array('SATNUM', case.satnum, 'd', per_line=20)
    text += _array('EQLNUM', case.eqlnum, 'd', per_line=20)

    text += '\nSOLUTION\nEQUIL\n'
    for fwl in case.fwl:
        text += f' {fwl:.3f} {DATUM_PRESSURE:g} {fwl:.3f} 0 /\n'
    text += 'RPTRST\n BASIC=2 /\n'
    text += '\nSUMMARY\nFOIP\n\nSCHEDULE\nTSTEP\n 0.001 /\nEND\n'
    return text


def write_deck(case: Case, cells: Cells, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{DECK_NAME}.DATA'
    path.write_text(deck_text(case, cells))
    return path
