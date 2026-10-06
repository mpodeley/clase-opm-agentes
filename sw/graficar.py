"""Log versus initialized water saturation, one figure per evaluation."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from sw.modelo import GRAVITY_BAR_PER_M, JFUNC_METRIC_CONSTANT, Case
from sw.pozo import WELLS, Cells

SURFACE = '#fcfcfb'
INK = '#0b0b0b'
SECONDARY = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'
LOG = '#898781'        # the reference: neutral
SIMULATED = '#2a78d6'  # the one series that changes between cases


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=10, length=0)


def _fwl_levels(case: Case, m: np.ndarray) -> list[float]:
    return sorted({case.fwl[i - 1] for i in np.unique(case.eqlnum[m])})


def _draw_fwl(ax, levels: list[float], top: float, base: float, x: float, ha: str, gap: float) -> None:
    """Free water levels on a depth axis: a line each when they are few, a band when they are many."""
    inside = [f for f in levels if top <= f <= base]
    if len(levels) > 3:
        lo, hi = max(levels[0], top), min(levels[-1], base)
        if lo < hi:
            ax.axhspan(lo, hi, color=GRID, alpha=0.7, linewidth=0)
            ax.text(x, lo - gap, f'FWL {levels[0]:,.0f} a {levels[-1]:,.0f} m', ha=ha, va='bottom',
                    fontsize=10, color=SECONDARY)
        return
    for fwl in inside:
        ax.axhline(fwl, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.text(x, fwl - gap, f'FWL {fwl:,.0f} m', ha=ha, va='bottom', fontsize=10, color=SECONDARY)


# One colour per well, in a fixed order: it follows the well in every figure of the class.
WELL_COLOR = {'19 SR': '#2a78d6', '19 A': '#eb6834', '19 BT2': '#1baf7a', 'F-12': '#eda100',
              'F-4': '#e87ba4', 'F-11 B': '#4a3aa7'}


def case_j(case: Case, cells: Cells) -> np.ndarray | None:
    """Leverett J of each cell under the case: height above its free water level times rock quality."""
    if case.jfunc is None:
        return None
    j = case.jfunc
    height = np.array(case.fwl)[case.eqlnum - 1] - cells.tvdss
    pc = GRAVITY_BAR_PER_M * np.maximum(height, 0.0)
    return pc * cells.k ** j.beta / cells.phi ** j.alpha / (j.surface_tension * JFUNC_METRIC_CONSTANT)


def _stairs(values: np.ndarray, depth: np.ndarray, dz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """A cell-by-cell curve against depth: each value held from the top to the bottom of its cell."""
    return np.repeat(values, 2), np.column_stack([depth - 0.5 * dz, depth + 0.5 * dz]).ravel()


def _track(ax, cells: Cells, sw_sim: np.ndarray, case: Case, well: str, result: dict) -> None:
    """One well: log and simulated water saturation against depth, with its free water level."""
    _style(ax)
    m = cells.of(well)
    depth = cells.tvdss[m]
    # A faulted well leaves the Hugin and comes back: break the lines where the hole skips ahead.
    cut = np.flatnonzero(np.diff(cells.md[m]) > 2.5) + 1
    for part in np.split(np.arange(m.sum()), cut):
        ax.fill_betweenx(depth[part], 0, 1, where=~cells.net[m][part], color=GRID, alpha=0.6,
                         linewidth=0, step='mid')
        # Both curves are cell values, so they are drawn as stairs: one tread per cell.
        ax.plot(*_stairs(cells.sw[m][part], depth[part], cells.dz[m][part]), color=LOG, linewidth=1.0)
        ax.plot(*_stairs(sw_sim[m][part], depth[part], cells.dz[m][part]), color=WELL_COLOR[well], linewidth=1.8)
    for fwl in _fwl_levels(case, m)[:3]:
        ax.axhline(fwl, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(['0', '0.5', '1'])
    spec = WELLS[well]
    ax.set_title(f'{well}\n{spec.logged.split()[-1]} · {result[f"rmse_{spec.slug}"]:.3f}',
                 fontsize=10, color=INK, loc='left')


def profiles(cells: Cells, sw_sim: np.ndarray, case: Case, result: dict, path: Path) -> Path:
    """Every well as a depth track on one depth scale, and the J function the case implies."""
    wells = list(WELLS)
    fig = plt.figure(figsize=(14, 6.8), facecolor=SURFACE)
    grid = fig.add_gridspec(1, len(wells) + 2, width_ratios=[1] * len(wells) + [0.45, 4.2], wspace=0.16,
                            left=0.055, right=0.985, top=0.80, bottom=0.10)
    top, base = cells.tvdss.min() - 8, max(cells.tvdss.max(), max(case.fwl)) + 8
    first = None
    for i, well in enumerate(wells):
        ax = fig.add_subplot(grid[0, i], sharey=first)
        first = first or ax
        _track(ax, cells, sw_sim, case, well, result)
        ax.tick_params(labelleft=(i == 0))
    first.set_ylim(base, top)
    first.set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    fig.text(0.055 + 0.5 * (0.985 - 0.055) * len(wells) / (len(wells) + 4.9), 0.025,
             'Sw por celda, una por metro de pozo: gris el perfil, color el simulado; fondo gris, roca no neta; trazos, FWL',
             ha='center', fontsize=9, color=SECONDARY)

    ax = fig.add_subplot(grid[0, -1])
    _style(ax)
    j = case_j(case, cells)
    if j is None:
        ax.text(0.5, 0.5, 'El caso no usa función J', transform=ax.transAxes, ha='center', color=MUTED)
    else:
        swl = case.swl if case.swl is not None else np.zeros(len(cells))
        for well in wells:
            m = cells.of(well) & cells.net & (j > 0)
            swn = (cells.sw[m] - swl[m]) / (1.0 - swl[m])
            ax.scatter(swn, j[m], s=9, color=WELL_COLOR[well], alpha=0.55, linewidths=0,
                       label=f'{well}' + (' (control)' if WELLS[well].role == 'control' else ''))
        for curve in case.curves:
            ax.plot(curve.sw, curve.pc, color=INK, linewidth=1.8)
        ax.set_yscale('log')
        ax.set_ylim(max(np.nanmin(j[j > 0]) * 0.5, 1e-2), np.nanmax(j) * 2)
        ax.set_xlim(-0.05 if case.swl is not None else 0, 1.02)
        ax.set_xlabel('Sw del perfil' + (', normalizada con el Swirr de cada celda' if case.swl is not None else ' (fracción)'),
                      fontsize=11, color=SECONDARY)
        ax.set_ylabel('J', fontsize=11, color=SECONDARY, rotation=0, labelpad=10)
        ax.legend(loc='upper right', frameon=False, fontsize=9, labelcolor=SECONDARY, markerscale=2)
        ax.set_title('J = Pc · √(k/φ) / σcosθ con el FWL del caso\nceldas netas de cada pozo y curva del caso (negro)',
                     fontsize=10, color=INK, loc='left')

    fig.suptitle(case.description, x=0.055, y=0.975, ha='left', fontsize=15, color=INK)
    fwl = ', '.join(f'{f:,.0f}' for f in sorted(set(case.fwl))[:3]) + (' …' if len(set(case.fwl)) > 3 else '')
    fig.text(0.055, 0.905, f'RMSE de ajuste {result["rmse_ajuste"]:.3f} (5 pozos previos a la producción) · '
             f'control {result["rmse_control"]:.3f} · {case.n_parameters} parámetros · FWL {fwl} m · '
             f'volumen poral de hidrocarburo {result["error_hcpv_ajuste"]:+.1%}',
             fontsize=10, color=SECONDARY)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    return path
