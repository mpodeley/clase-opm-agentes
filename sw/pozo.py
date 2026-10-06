"""Well logs on the simulation grid: interpreted log + well path -> one cell per metre of hole.

Each cell carries its own depth and rock properties, so the model is a string of cells
along the well path instead of a vertical stack. Equilibration only needs depth and rock
per cell, which makes the same construction valid for a vertical and a horizontal well.

Only the Hugin Formation is kept. Five wells were logged before first oil (12 February 2008)
and are the ones a case is fitted to. Two wells are controls that no case ever sees:
15/9-F-5, logged in July 2008 with 5% of the field's final oil produced and before it started
injecting, stands for the initial state; 15/9-F-11 B, logged in 2013 with 77% produced, is swept.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from pathlib import Path

import lasio
import numpy as np

DATA = Path(__file__).resolve().parent.parent / 'datos' / 'volve'
KB = 54.9            # m, kelly bushing of the Maersk Inspirer (the F wells)
CELL_LENGTH = 1.0    # m of measured depth per cell
MIN_PERM = 1e-4      # mD, floor so that sqrt(k/phi) stays finite
MIN_PORO = 1e-3      # keeps tight cells active in the simulator
HUGIN_TOP = 'Hugin Fm. VOLVE Top'
# Net sand where the file has no SAND_FLAG. These cut-offs reproduce the operator's flag in
# 96 to 98% of the samples of the wells that do carry it.
NET_MAX_VSH = 0.5
NET_MIN_PHI = 0.10


@dataclass(frozen=True)
class WellSpec:
    name: str               # short name used in tables and plots
    log: str                # interpreted log, relative to DATA
    trajectory: str | None  # survey file; None = interpolate between the formation picks
    role: str               # 'ajuste' (fitted), or a control never shown to a case:
                            # 'control_inicial' (before sweep) or 'control_barrido' (after)
    logged: str             # when the reservoir section was logged
    perm: str | None = None  # the operator's 2009 revision of permeability, where there is one

    @property
    def picks_name(self) -> str:
        return f'NO 15/9-{self.name}'

    @property
    def slug(self) -> str:
        return self.name.replace(' ', '-')


WELLS = {w.name: w for w in (
    WellSpec('19 SR', 'perfiles/15_9-19 SR/15_9-19_SR_CPI.las', None, 'ajuste', '1993'),
    WellSpec('19 A', 'perfiles/15_9-19 A/15_9-19_A_CPI.las', None, 'ajuste', '1997'),
    WellSpec('19 BT2', 'perfiles/15_9-19 BT2/15_9-19_BT2_CPI.las', None, 'ajuste', '1998',
             'perfiles/15_9-19 BT2/KLOGH_NEW.las'),
    WellSpec('F-12', 'perfiles/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS', 'trayectorias/F-12_ACTUAL',
             'ajuste', '2007', 'perfiles/15_9-F-12/KLOGH_NEW.las'),
    WellSpec('F-4', 'perfiles/15_9-F-4/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS', 'trayectorias/F-4_ACTUAL',
             'ajuste', 'febrero de 2008', 'perfiles/15_9-F-4/KLOGH_NEW.las'),
    WellSpec('F-5', 'perfiles/15_9-F-5/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS', 'trayectorias/F-5_ACTUAL',
             'control_inicial', 'julio de 2008', 'perfiles/15_9-F-5/KLOGH_NEW.las'),
    WellSpec('F-11 B', 'perfiles/15_9-F-11 B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS', 'trayectorias/F-11 B_ACTUAL',
             'control_barrido', '2013'),
)}
ROLES = ('ajuste', 'control_inicial', 'control_barrido')
FIT_WELLS = [w.name for w in WELLS.values() if w.role == 'ajuste']
CONTROL_WELLS = [w.name for w in WELLS.values() if w.role != 'ajuste']


@dataclass(frozen=True)
class Cells:
    """Struct of arrays, one entry per cell. Depths are metres below sea level, positive down."""
    well: np.ndarray    # str
    md: np.ndarray      # m, cell centre
    tvdss: np.ndarray   # m, cell centre
    length: np.ndarray  # m of hole in the cell
    dz: np.ndarray      # m, vertical extent of the cell
    x: np.ndarray       # m, UTM easting
    y: np.ndarray       # m, UTM northing
    phi: np.ndarray     # fraction
    k: np.ndarray       # mD
    vsh: np.ndarray     # fraction
    net: np.ndarray     # bool, net sand
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


# ---------------------------------------------------------------------------------------------
# Formation picks and well paths

@lru_cache(maxsize=None)
def load_picks(picks_name: str) -> tuple[tuple[float, float, float, float, str], ...]:
    """(MD, TVDSS, easting, northing, surface) for one well, sorted by MD. TVDSS is positive down."""
    picks = []
    for line in (DATA / 'topes' / 'Well_picks_Volve_v1.dat').read_text(errors='replace').splitlines():
        if line[2:26].strip() != picks_name:
            continue
        numbers = line[78:].split()
        try:
            picks.append((float(numbers[0]), -float(numbers[2]), float(numbers[-3]), float(numbers[-2]),
                          line[27:67].strip()))
        except (ValueError, IndexError):
            continue
    return tuple(sorted(picks, key=lambda p: (p[0], not p[4].endswith('Base'))))


def hugin_intervals(picks_name: str) -> list[tuple[float, float]]:
    """(top MD, base MD) of every stretch of Hugin the well crosses. A faulted well has several."""
    out, top = [], None
    for md, *_, surface in load_picks(picks_name):
        if surface == HUGIN_TOP and top is None:
            top = md
        elif top is not None and surface != HUGIN_TOP and md > top:
            out.append((top, md))
            top = None
    return out


def load_trajectory(path: Path) -> np.ndarray:
    """Columns: MD, TVD (both m RKB), easting, northing."""
    return np.loadtxt(path, skiprows=2, usecols=(0, 3, 6, 7))


def position(well: str, md: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """TVDSS, easting and northing at measured depths `md`.

    The F wells have a survey. The exploration wells do not have one in the public mirrors, so
    their path is interpolated between the formation picks, which carry depth and position.
    """
    spec = WELLS[well]
    if spec.trajectory:
        t = load_trajectory(DATA / spec.trajectory)
        return np.interp(md, t[:, 0], t[:, 1]) - KB, np.interp(md, t[:, 0], t[:, 2]), np.interp(md, t[:, 0], t[:, 3])
    p = np.array([row[:4] for row in load_picks(spec.picks_name)])
    p = p[np.unique(p[:, 0], return_index=True)[1]]
    return np.interp(md, p[:, 0], p[:, 1]), np.interp(md, p[:, 0], p[:, 2]), np.interp(md, p[:, 0], p[:, 3])


# ---------------------------------------------------------------------------------------------
# Logs

def _read_las(path: Path) -> dict[str, np.ndarray]:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        las = lasio.read(path, engine='normal')
    curves = {c.mnemonic.upper(): np.asarray(c.data, dtype=float) for c in las.curves}
    curves['MD'] = np.asarray(las.index, dtype=float)
    return curves


def _read_dlis(path: Path) -> dict[str, np.ndarray]:
    from dlisio import dlis   # imported here: only one well needs it
    with dlis.load(str(path)) as (logical_file, *_):
        frame = logical_file.frames[0]
        data = frame.curves()
        units = {c.name: (c.units or '') for c in frame.channels}
    curves = {name.upper(): np.asarray(data[name], dtype=float) for name in data.dtype.names}
    scale = 0.00254 if units.get('DEPTH', '').strip() == '0.1 in' else 1.0
    curves['MD'] = curves['DEPTH'] * scale
    for values in curves.values():
        values[values == -999.25] = np.nan
    return curves


@lru_cache(maxsize=None)
def read_curves(relative_path: str) -> dict[str, np.ndarray]:
    """Every curve of a log file by mnemonic, plus 'MD' in metres. Works for LAS and DLIS."""
    path = DATA / relative_path
    return _read_dlis(path) if path.suffix.upper() == '.DLIS' else _read_las(path)


def load_log(well: str) -> dict[str, np.ndarray]:
    """Interpreted log at its native sampling, with depth and position, and a net sand flag."""
    curves = read_curves(WELLS[well].log)
    md = curves['MD']
    tvdss, x, y = position(well, md)
    phi, vsh = curves['PHIF'], curves['VSH']
    if 'SAND_FLAG' in curves:
        net = curves['SAND_FLAG'] > 0.5
    else:
        net = (vsh < NET_MAX_VSH) & (phi > NET_MIN_PHI)
    k = curves['KLOGH']
    if WELLS[well].perm:
        # In F-12 the permeability of the 2007 file is about 40 times lower than the 2009 revision,
        # and J goes with its square root: the revision is used wherever the operator made one.
        revised = read_curves(WELLS[well].perm)
        inside = (md >= revised['MD'][0]) & (md <= revised['MD'][-1])
        k = np.where(inside, np.interp(md, revised['MD'], revised['KLOGH_NEW']), k)
    return {'md': md, 'tvdss': tvdss, 'x': x, 'y': y, 'phi': phi, 'k': k, 'vsh': vsh,
            'sw': curves['SW'], 'net': net}


@lru_cache(maxsize=None)
def load_cells(well: str, cell_length: float = CELL_LENGTH) -> Cells:
    """Upscale the Hugin of one well to cells of `cell_length` metres of hole.

    Porosity and shale volume are arithmetic means, permeability is a geometric mean and
    water saturation is weighted by porosity, so that the cell keeps the water volume of the log.
    A cell is net when at least half of its samples are. A cell with less than half of its
    samples valid is dropped.
    """
    log = load_log(well)
    rows = []
    for top, base in hugin_intervals(WELLS[well].picks_name):
        edges = np.arange(top, min(base, log['md'][-1]) + 1e-9, cell_length)
        for a, b in zip(edges[:-1], edges[1:]):
            m = (log['md'] >= a) & (log['md'] < b)
            ok = m & np.isfinite(log['phi']) & np.isfinite(log['k']) & np.isfinite(log['sw'])
            if m.sum() == 0 or ok.sum() < 0.5 * m.sum():
                continue
            phi = log['phi'][ok]
            weight = np.maximum(phi, MIN_PORO)
            (z_a, z_c, z_b), xs, ys = position(well, np.array([a, 0.5 * (a + b), b]))
            rows.append((
                0.5 * (a + b), z_c, b - a, max(z_b - z_a, 0.05), xs[1], ys[1],
                max(phi.mean(), MIN_PORO),
                float(np.exp(np.log(np.maximum(log['k'][ok], MIN_PERM)).mean())),
                float(np.nanmean(log['vsh'][ok])),
                float(log['net'][ok].mean() >= 0.5),
                float(np.clip((weight * log['sw'][ok]).sum() / weight.sum(), 0.0, 1.0)),
            ))
    md, tvdss, length, dz, x, y, phi, k, vsh, net, sw = (np.array(c) for c in zip(*rows))
    return Cells(well=np.full(len(md), well), md=md, tvdss=tvdss, length=length, dz=dz, x=x, y=y,
                 phi=phi, k=k, vsh=vsh, net=net.astype(bool), sw=sw)


def load_all() -> Cells:
    return concatenate([load_cells(w) for w in WELLS])
