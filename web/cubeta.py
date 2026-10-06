"""Is there a basin at the base of the Hugin under 15/9-F-4 that could hold perched water?

    uv run web/cubeta.py [output_dir]      default: slides/img

The mapped base of the Hugin is filled like a terrain: water sits in every closed low of the
base, up to the level where it would spill. Steep steps of the surface are taken as sealing
faults, so a block that dips into a fault counts as closed on that side. The answer depends on
how steep a step has to be to count as a fault, and the script reports it for several thresholds.

Writes cubeta.png and cubeta.json.
"""
from __future__ import annotations

import heapq
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contexto import BLUES, FWL_DECK  # noqa: E402
from sw import pozo  # noqa: E402
from sw.graficar import AXIS, GRID, INK, MUTED, SECONDARY, SURFACE, WELL_COLOR, _style  # noqa: E402

SPACING = 12.5                       # m between map nodes
THRESHOLDS = (0.6, 0.8, 1.0, 1.5)    # slope of the base above which a step counts as a sealing fault
SHOWN = 0.8                          # the threshold drawn in the figure
PURGED_WATER_DECK = 3025.0           # field deck, EQUIL region "main structure, purged water"
REGIONAL_FWL = 3146.0                # the fitted regional level (case P)
LOCAL_FWL = 3033.0                   # the local level the logs of F-4 ask for (case P)


def load_surface(name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Depth, easting and northing on the inline/crossline lattice; NaN where the map has no node."""
    a = np.loadtxt(pozo.DATA / 'mapas' / name, delimiter=',', skiprows=1)
    il, xl = a[:, 0].astype(int), a[:, 1].astype(int)
    shape = (il.max() - il.min() + 1, xl.max() - xl.min() + 1)
    z, x, y = (np.full(shape, np.nan) for _ in range(3))
    z[il - il.min(), xl - xl.min()], x[il - il.min(), xl - xl.min()], y[il - il.min(), xl - xl.min()] = a[:, 4], a[:, 2], a[:, 3]
    return z, x, y


def spill_level(depth: np.ndarray, barrier: np.ndarray) -> np.ndarray:
    """Level up to which water can sit above each node of the base before it escapes.

    Priority flood from the edge of the mapped area. `barrier` nodes are walls: water neither
    crosses them nor escapes through them.
    """
    valid = ~np.isnan(depth)
    open_ = valid & ~barrier
    rows, cols = depth.shape
    level = np.full(depth.shape, np.nan)
    seen = np.zeros(depth.shape, dtype=bool)
    heap: list[tuple[float, int, int]] = []
    inner = np.zeros(depth.shape, dtype=bool)
    inner[1:-1, 1:-1] = valid[:-2, 1:-1] & valid[2:, 1:-1] & valid[1:-1, :-2] & valid[1:-1, 2:]
    for i, j in np.argwhere(open_ & ~inner):
        heapq.heappush(heap, (-depth[i, j], i, j))   # shallow first: elevation = -depth
        seen[i, j], level[i, j] = True, depth[i, j]
    while heap:
        elevation, i, j = heapq.heappop(heap)
        for k, m in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= k < rows and 0 <= m < cols and open_[k, m] and not seen[k, m]:
                seen[k, m] = True
                level[k, m] = min(depth[k, m], -elevation)   # cannot be deeper than the path out
                heapq.heappush(heap, (-level[k, m], k, m))
    return level


def analyse() -> dict:
    base, x, y = load_surface('Hugin_Fm_Base.csv')
    gy, gx = np.gradient(base, SPACING)
    slope = np.hypot(gx, gy)
    valid = ~np.isnan(base)
    nodes = np.argwhere(valid)
    tree = cKDTree(np.column_stack([x[valid], y[valid]]))
    table, kept = [], None
    for threshold in THRESHOLDS:
        barrier = valid & (slope > threshold)
        level = spill_level(base, barrier)
        column = base - level                     # trapped water column above the base
        labels, _ = ndimage.label(np.nan_to_num(column) > 1.0)
        row = {'umbral': threshold, 'grados': float(np.degrees(np.arctan(threshold)))}
        for well in pozo.FIT_WELLS:
            _, bottom = pozo.hugin_intervals(pozo.WELLS[well].picks_name)[0]
            z, xw, yw = pozo.position(well, np.array([bottom]))
            i, j = nodes[tree.query([xw[0], yw[0]])[1]]
            if barrier[i, j]:                     # the well bottom sits on the step: take the nearest open node
                free = np.argwhere(valid & ~barrier)
                i, j = free[np.argmin((free[:, 0] - i) ** 2 + (free[:, 1] - j) ** 2)]
            area = float((labels == labels[i, j]).sum() * SPACING ** 2 / 1e6) if labels[i, j] else 0.0
            row[well] = {'columna_m': float(np.nan_to_num(column[i, j])), 'derrame_m': float(level[i, j]),
                         'area_km2': area}
        table.append(row)
        if threshold == SHOWN:
            kept = (base, x, y, barrier, column, level)
    return {'tabla': table, 'mapa': kept}


def figure(result: dict, path: Path) -> None:
    base, x, y, barrier, column, level = result['mapa']
    top, xt, yt = load_surface('Hugin_Fm_Top.csv')
    cells = pozo.load_cells('F-4')
    shown = next(r for r in result['tabla'] if r['umbral'] == SHOWN)['F-4']
    x0, y0 = cells.x[-1], cells.y[-1]

    fig, (ax, sec) = plt.subplots(1, 2, figsize=(13, 6.2), facecolor=SURFACE,
                                  gridspec_kw={'width_ratios': [1, 1.15], 'left': 0.06, 'right': 0.98,
                                               'top': 0.83, 'bottom': 0.11, 'wspace': 0.2})
    _style(ax)
    ax.grid(False)
    window = (np.abs(x - x0) < 700) & (np.abs(y - y0) < 700) & ~np.isnan(base)
    filled = ax.tricontourf(x[window] - x0, y[window] - y0, base[window], levels=np.arange(2900, 3351, 25),
                            cmap=BLUES, extend='both')
    ax.tricontour(x[window] - x0, y[window] - y0, base[window], levels=np.arange(2900, 3351, 25),
                  colors=SURFACE, linewidths=0.3)
    fault = window & barrier
    ax.scatter(x[fault] - x0, y[fault] - y0, s=3, color=INK, linewidths=0, alpha=0.55)
    pool = window & (np.nan_to_num(column) > 1.0) & (np.abs(level - shown['derrame_m']) < 0.5)
    ax.scatter(x[pool] - x0, y[pool] - y0, s=9, color='#eb6834', linewidths=0)
    ax.plot(cells.x - x0, cells.y - y0, color=WELL_COLOR['F-4'], linewidth=3, solid_capstyle='round')
    ax.plot(0, 0, 'o', ms=7, color=WELL_COLOR['F-4'], markeredgecolor=SURFACE, markeredgewidth=1.3)
    ax.annotate('F-4, base del Hugin', (0, 0), xytext=(-12, 14), textcoords='offset points', fontsize=10, color=INK,
                ha='right', bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 1.5, 'alpha': 0.85})
    ax.set_xlim(-600, 600)
    ax.set_ylim(-600, 600)
    ax.set_aspect('equal')
    ax.set_xlabel('Este desde F-4 (m)', fontsize=10, color=SECONDARY)
    ax.set_ylabel('Norte desde F-4 (m)', fontsize=10, color=SECONDARY)
    bar = fig.colorbar(filled, ax=ax, shrink=0.8, pad=0.02)
    bar.set_label('Base del Hugin (m TVDSS)', fontsize=9, color=SECONDARY)
    bar.ax.invert_yaxis()
    bar.ax.tick_params(colors=MUTED, labelsize=8, length=0)
    bar.outline.set_visible(False)
    ax.set_title('En planta: en negro, escalones tomados como falla;\nen naranja, la cubeta contra la falla',
                 fontsize=10.5, color=INK, loc='left')

    # Section through the bottom of F-4, across the fault (along the crossline direction, pointing east).
    _style(sec)
    valid_b, valid_t = ~np.isnan(base), ~np.isnan(top)
    tree_b = cKDTree(np.column_stack([x[valid_b], y[valid_b]]))
    tree_t = cKDTree(np.column_stack([xt[valid_t], yt[valid_t]]))
    direction = np.array([12.1286, -3.0244]) / 12.5
    s = np.arange(-450, 351, 12.5)
    line = np.column_stack([x0 + s * direction[0], y0 + s * direction[1]])
    base_line = base[valid_b][tree_b.query(line)[1]]
    top_line = top[valid_t][tree_t.query(line)[1]]
    sec.fill_between(s, top_line, base_line, color=GRID, alpha=0.7, linewidth=0)
    sec.plot(s, top_line, color=SECONDARY, linewidth=1.2, linestyle=(0, (5, 2)))
    sec.plot(s, base_line, color=SECONDARY, linewidth=1.4)
    spill = shown['derrame_m']
    wet = (base_line > spill) & (s <= 40) & (s > -200)
    sec.fill_between(s, spill, base_line, where=wet, color='#eb6834', alpha=0.45, linewidth=0)
    sec.plot([s[wet].min() - 30, 60], [spill, spill], color='#c24b22', linewidth=1.4)
    sec.text(s[wet].min() - 36, spill, f'derrame de la cubeta: {spill:,.0f} m', fontsize=9.5, color=INK, ha='right', va='center')
    along = (cells.x - x0) * direction[0] + (cells.y - y0) * direction[1]
    points = sec.scatter(along, cells.tvdss, c=cells.sw, cmap=BLUES, vmin=0, vmax=1, s=22, linewidths=0, zorder=4)
    sec.plot([150, 350], [PURGED_WATER_DECK] * 2, color=SECONDARY, linewidth=0.9, linestyle=(0, (2, 2)))
    sec.text(345, PURGED_WATER_DECK - 3, f'modelo de campo: {PURGED_WATER_DECK:,.0f} m', fontsize=9, color=SECONDARY, ha='right')
    sec.plot([-30, 60], [LOCAL_FWL] * 2, color=INK, linewidth=1.4)
    sec.text(66, LOCAL_FWL + 1, f'ajuste con el perfil: {LOCAL_FWL:,.0f} m', fontsize=9.5, color=INK, va='center')
    sec.axhline(REGIONAL_FWL, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
    sec.text(-445, REGIONAL_FWL - 3, f'nivel de agua libre regional: {REGIONAL_FWL:,.0f} m', fontsize=9, color=SECONDARY)
    sec.text(-300, np.interp(-300, s, top_line) + 6, 'tope del Hugin', fontsize=9, color=SECONDARY, va='top')
    sec.text(-440, np.interp(-440, s, base_line) + 5, 'base del Hugin', fontsize=9, color=SECONDARY, va='top')
    sec.text(240, 3185, 'bloque bajo', fontsize=9, color=MUTED, ha='center')
    sec.set_xlim(-450, 350)
    sec.set_ylim(3220, 2900)
    sec.set_xlabel('Distancia desde la base de F-4, de oeste a este (m)', fontsize=10, color=SECONDARY)
    sec.set_ylabel('Profundidad (m TVDSS)', fontsize=10, color=SECONDARY)
    bar = fig.colorbar(points, ax=sec, shrink=0.8, pad=0.02)
    bar.set_label('Sw del perfil de F-4', fontsize=9, color=SECONDARY)
    bar.ax.tick_params(colors=MUTED, labelsize=8, length=0)
    bar.outline.set_visible(False)
    sec.set_title('En sección: el bloque inclina hacia la falla\ny la base queda por debajo del nivel de derrame',
                  fontsize=10.5, color=INK, loc='left')
    fig.suptitle('¿Agua colgada en la base de F-4? La base del Hugin, llenada como un terreno',
                 x=0.06, y=0.965, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'slides' / 'img'
    out.mkdir(parents=True, exist_ok=True)
    result = analyse()
    figure(result, out / 'cubeta.png')
    (out / 'cubeta.json').write_text(json.dumps(result['tabla'], indent=1))
    print('umbral  ' + '  '.join(f'{w:>16s}' for w in pozo.FIT_WELLS) + '   (columna de agua atrapable / nivel de derrame, m)')
    for row in result['tabla']:
        print(f'{row["umbral"]:5.2f}   ' + '  '.join(f'{row[w]["columna_m"]:6.1f} / {row[w]["derrame_m"]:7.1f}' for w in pozo.FIT_WELLS))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
