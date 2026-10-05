"""Log versus initialized water saturation, one figure per evaluation."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from sw.modelo import Case
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


def _track(ax, cells: Cells, sw_sim: np.ndarray, case: Case, m: np.ndarray, title: str) -> None:
    """One well: log and simulated water saturation against depth, with contacts and formations."""
    _style(ax)
    depth = cells.tvdss[m]
    ax.plot(cells.sw[m], depth, color=LOG, linewidth=1.1, label='Perfil')
    ax.plot(sw_sim[m], depth, color=SIMULATED, linewidth=1.8, label='Simulado')
    _draw_fwl(ax, _fwl_levels(case, m), depth.min(), depth.max(), 0.02, 'left', 0.006 * np.ptp(depth))
    zones = cells.zone[m]
    last = -np.inf
    for i in np.flatnonzero(np.r_[True, zones[1:] != zones[:-1]]):
        if i:
            ax.axhline(depth[i], color=AXIS, linewidth=0.6)
        if depth[i] - last > 0.035 * np.ptp(depth):   # skip labels that would overprint
            ax.text(1.03, depth[i], zones[i], fontsize=10, color=MUTED, va='top', clip_on=False)
            last = depth[i]
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.set_xlabel('Sw (fracción)', fontsize=11, color=SECONDARY)
    ax.set_title(title, fontsize=12, color=INK, loc='left')


def profiles(cells: Cells, sw_sim: np.ndarray, case: Case, result: dict, path: Path) -> Path:
    """Both wells as depth tracks. F-11 B has a horizontal section, which piles up near 2,865 m."""
    fit, held = (next(w.name for w in WELLS.values() if w.role == r) for r in ('ajuste', 'validacion'))
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 6.6), facecolor=SURFACE,
                                      gridspec_kw={'wspace': 0.42, 'left': 0.07, 'right': 0.88,
                                                   'top': 0.84, 'bottom': 0.09})
    _track(left, cells, sw_sim, case, cells.of(fit), f'{fit} · ajuste · RMSE {result["rmse_ajuste"]:.3f}')
    _track(right, cells, sw_sim, case, cells.of(held),
           f'{held} · validación · RMSE {result["rmse_validacion"]:.3f}')
    left.set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    left.legend(loc='lower left', frameon=False, fontsize=10, labelcolor=SECONDARY)

    fig.suptitle(case.description, x=0.07, y=0.985, ha='left', fontsize=15, color=INK)
    fig.text(0.07, 0.905, f'{case.n_parameters} parámetros · error en volumen poral de hidrocarburo: '
             f'{result["error_hcpv_ajuste"]:+.1%} en {fit}, {result["error_hcpv_validacion"]:+.1%} en {held}',
             fontsize=11, color=SECONDARY)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    return path


def log_only(cells: Cells, well: str, path: Path) -> Path:
    """The problem statement: the interpreted log of one well, with nothing simulated on it."""
    m = cells.of(well)
    fig, axes = plt.subplots(1, 3, figsize=(10, 6.2), sharey=True, facecolor=SURFACE,
                             gridspec_kw={'wspace': 0.08, 'left': 0.08, 'right': 0.88, 'top': 0.88, 'bottom': 0.09})
    tracks = [(cells.sw[m], 'Sw (fracción)', (0, 1), False),
              (cells.phi[m], 'Porosidad (fracción)', (0, 0.35), False),
              (cells.k[m], 'Permeabilidad (mD)', (1e-3, 1e4), True)]
    for ax, (values, label, limits, log_scale) in zip(axes, tracks):
        _style(ax)
        ax.plot(values, cells.tvdss[m], color=SIMULATED if label.startswith('Sw') else LOG, linewidth=1.4)
        if log_scale:
            ax.set_xscale('log')
        ax.set_xlim(*limits)
        ax.set_xlabel(label, fontsize=11, color=SECONDARY)
    zones = cells.zone[m]
    for i in np.flatnonzero(np.r_[True, zones[1:] != zones[:-1]]):
        axes[-1].text(1.04, cells.tvdss[m][i], zones[i], fontsize=11, color=MUTED, va='top',
                      transform=axes[-1].get_yaxis_transform(), clip_on=False)
        if i:
            for ax in axes:
                ax.axhline(cells.tvdss[m][i], color=AXIS, linewidth=0.6)
    axes[0].invert_yaxis()
    axes[0].set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    fig.suptitle(f'15/9-{well}: perfil interpretado, una celda por metro de pozo',
                 x=0.08, y=0.96, ha='left', fontsize=15, color=INK)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    return path
