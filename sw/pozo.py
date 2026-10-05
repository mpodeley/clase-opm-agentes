"""Well logs on the simulation grid: LAS + trajectory -> one cell per metre of hole.

Each cell carries its own depth and rock properties, so the model is a string of cells
along the well path instead of a vertical stack. Equilibration only needs depth and rock
per cell, which makes the same construction valid for a deviated and a horizontal well.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, fields, replace
from pathlib import Path

import lasio
import numpy as np

DATA = Path(__file__).resolve().parent.parent / 'datos' / 'volve'
KB = 54.9            # m, kelly bushing elevation of the Maersk Inspirer for both wells
CELL_LENGTH = 1.0    # m of measured depth per cell
MIN_PERM = 1e-4      # mD, floor so that sqrt(k/phi) stays finite
MIN_PORO = 1e-3      # keeps tight cells active in the simulator
START_PICK = 'Hugin Fm. VOLVE Top'


@dataclass(frozen=True)
class WellSpec:
    name: str        # short name used in tables and plots
    las: str
    trajectory: str
    picks_name: str  # name in the picks file
    role: str        # 'ajuste' (fitted) or 'validacion' (held out)
    logged: str      # when the log was acquired, for the record


WELLS = {
    'F-12': WellSpec('F-12', 'perfiles/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
                     'trayectorias/F-12_ACTUAL', 'NO 15/9-F-12', 'ajuste', '2007'),
    'F-11 B': WellSpec('F-11 B', 'perfiles/15_9-F-11 B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
                       'trayectorias/F-11 B_ACTUAL', 'NO 15/9-F-11 B', 'validacion', '2013'),
}


@dataclass(frozen=True)
class Cells:
    """Struct of arrays, one entry per cell. Depths are metres below sea level, positive down."""
    well: np.ndarray    # str
    zone: np.ndarray    # str, formation from the picks file
    md: np.ndarray      # m, cell centre
    tvdss: np.ndarray   # m, cell centre
    length: np.ndarray  # m of hole in the cell
    dz: np.ndarray      # m, vertical extent of the cell
    x: np.ndarray       # m, UTM easting
    y: np.ndarray       # m, UTM northing
    phi: np.ndarray     # fraction
    k: np.ndarray       # mD
    vsh: np.ndarray     # fraction
    sw: np.ndarray      # fraction, NaN where the log is hidden from the case

    def __len__(self) -> int:
        return len(self.md)

    def mask(self, m: np.ndarray) -> 'Cells':
        return Cells(**{f.name: getattr(self, f.name)[m] for f in fields(self)})

    def of(self, well: str) -> np.ndarray:
        return self.well == well

    def hide_sw(self, wells: list[str]) -> 'Cells':
        sw = self.sw.copy()
        sw[np.isin(self.well, wells)] = np.nan
        return replace(self, sw=sw)


def concatenate(parts: list[Cells]) -> Cells:
    return Cells(**{f.name: np.concatenate([getattr(p, f.name) for p in parts]) for f in fields(Cells)})


def load_trajectory(path: Path) -> np.ndarray:
    """Columns: MD, TVD (both m RKB), easting, northing."""
    return np.loadtxt(path, skiprows=2, usecols=(0, 3, 6, 7))


def load_picks(picks_name: str) -> list[tuple[float, str]]:
    """(MD, surface name) for one well, sorted by MD with a Base ahead of a Top at the same depth."""
    picks = []
    for line in (DATA / 'topes' / 'Well_picks_Volve_v1.dat').read_text(errors='replace').splitlines():
        if line[2:26].strip() != picks_name:
            continue
        try:
            md = float(line[78:86])
        except ValueError:
            continue
        picks.append((md, line[27:67].strip()))
    return sorted(picks, key=lambda p: (p[0], not p[1].endswith('Base')))


def zone_name(surface: str) -> str:
    short = surface.replace(' VOLVE', '').replace(' Fm.', '').replace(' GP.', '')
    if short.endswith(' Base'):
        return 'bajo ' + short.removesuffix(' Base')
    return short.removesuffix(' Top')


def zones_at(md: np.ndarray, picks: list[tuple[float, str]]) -> np.ndarray:
    out = np.full(len(md), 'sin tope', dtype=object)
    for pick_md, surface in picks:
        out[md >= pick_md] = zone_name(surface)
    return out.astype(str)


def start_md(picks: list[tuple[float, str]]) -> float:
    return min(md for md, surface in picks if surface == START_PICK)


def load_log(well: str) -> dict[str, np.ndarray]:
    """Interpreted log at its native sampling, with depth and position from the trajectory."""
    spec = WELLS[well]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        las = lasio.read(DATA / spec.las)
    traj = load_trajectory(DATA / spec.trajectory)
    md = np.asarray(las['DEPTH'], dtype=float)
    return {
        'md': md,
        'tvdss': np.interp(md, traj[:, 0], traj[:, 1]) - KB,
        'x': np.interp(md, traj[:, 0], traj[:, 2]),
        'y': np.interp(md, traj[:, 0], traj[:, 3]),
        'phi': np.asarray(las['PHIF'], dtype=float),
        'k': np.asarray(las['KLOGH'], dtype=float),
        'vsh': np.asarray(las['VSH'], dtype=float),
        'sw': np.asarray(las['SW'], dtype=float),
    }


def load_cells(well: str, cell_length: float = CELL_LENGTH) -> Cells:
    """Upscale one well to cells of `cell_length` metres of hole, from the top of the Hugin down.

    Porosity and shale volume are arithmetic means, permeability is a geometric mean and
    water saturation is weighted by porosity, so that the cell keeps the water volume of the log.
    A cell with less than half of its samples valid is dropped.
    """
    spec = WELLS[well]
    log = load_log(well)
    picks = load_picks(spec.picks_name)
    md0 = start_md(picks)
    traj = load_trajectory(DATA / spec.trajectory)
    edges = np.arange(md0, log['md'][-1] + 1e-9, cell_length)
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (log['md'] >= a) & (log['md'] < b)
        ok = m & np.isfinite(log['phi']) & np.isfinite(log['k']) & np.isfinite(log['sw'])
        if m.sum() == 0 or ok.sum() < 0.5 * m.sum():
            continue
        phi = log['phi'][ok]
        centre = 0.5 * (a + b)
        tvd_a, tvd_b = np.interp([a, b], traj[:, 0], traj[:, 1])
        weight = np.maximum(phi, MIN_PORO)
        rows.append((
            centre,
            np.interp(centre, traj[:, 0], traj[:, 1]) - KB,
            b - a,
            max(tvd_b - tvd_a, 0.05),
            np.interp(centre, traj[:, 0], traj[:, 2]),
            np.interp(centre, traj[:, 0], traj[:, 3]),
            max(phi.mean(), MIN_PORO),
            float(np.exp(np.log(np.maximum(log['k'][ok], MIN_PERM)).mean())),
            float(np.nanmean(log['vsh'][ok])),
            float(np.clip((weight * log['sw'][ok]).sum() / weight.sum(), 0.0, 1.0)),
        ))
    md, tvdss, length, dz, x, y, phi, k, vsh, sw = (np.array(c) for c in zip(*rows))
    return Cells(well=np.full(len(md), well), zone=zones_at(md, picks), md=md, tvdss=tvdss,
                 length=length, dz=dz, x=x, y=y, phi=phi, k=k, vsh=vsh, sw=sw)


def load_all() -> Cells:
    return concatenate([load_cells(w) for w in WELLS])
