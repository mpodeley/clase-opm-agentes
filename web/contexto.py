"""Context figures for the public page and the first block of the class.

    uv run web/contexto.py [output_dir]      default: slides/img

Writes mapa-hugin.png, secciones.png, perfil-f12.png, perfil-f11b.png and produccion.png,
all from the pinned Volve files in datos/volve/.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sw import pozo  # noqa: E402
from sw.graficar import AXIS, GRID, INK, MUTED, SECONDARY, SURFACE, _style, log_only  # noqa: E402

# One hue, light to dark: shallow to deep on the map, oil to water on the wells.
BLUES = LinearSegmentedColormap.from_list('blues', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
SERIES = {'Petróleo': '#2a78d6', 'Agua producida': '#eb6834', 'Agua inyectada': '#1baf7a'}
HIGHLIGHT = '#c24b22'
KM = 1000.0


def hugin_map() -> np.ndarray:
    """Columns: easting, northing, depth of the top of the Hugin in m TVDSS."""
    return np.loadtxt(pozo.DATA / 'mapas' / 'Hugin_Fm_Top.csv', delimiter=',', skiprows=1)[:, 2:5]


def hugin_entries() -> dict[str, tuple[float, float]]:
    """Where each well with a pick first enters the Hugin: short name -> (easting, northing)."""
    out: dict[str, tuple[float, float]] = {}
    for line in (pozo.DATA / 'topes' / 'Well_picks_Volve_v1.dat').read_text(errors='replace').splitlines():
        name = line[2:26].strip().removeprefix('NO 15/9-')
        if line[27:67].strip() != pozo.START_PICK or name in out:
            continue
        fields = line[78:].split()
        try:
            out[name] = (float(fields[-3]), float(fields[-2]))
        except (ValueError, IndexError):
            continue
    return out


def path_in_reservoir(well: str) -> np.ndarray:
    """Trajectory stations over the logged interval: MD, TVDSS, easting, northing."""
    spec = pozo.WELLS[well]
    traj = pozo.load_trajectory(pozo.DATA / spec.trajectory)
    cells = pozo.load_cells(well)
    md = np.linspace(cells.md[0], cells.md[-1], 400)
    return np.column_stack([md, np.interp(md, traj[:, 0], traj[:, 1]) - pozo.KB,
                            np.interp(md, traj[:, 0], traj[:, 2]), np.interp(md, traj[:, 0], traj[:, 3])])


def figure_map(surface: np.ndarray, path: Path) -> None:
    x0, y0 = 433500.0, 6476900.0
    fig, ax = plt.subplots(figsize=(9.6, 7.2), facecolor=SURFACE)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    _style(ax)
    ax.grid(False)
    filled = ax.tricontourf((surface[:, 0] - x0) / KM, (surface[:, 1] - y0) / KM, surface[:, 2],
                            levels=np.arange(2700, 3401, 50), cmap=BLUES)
    for name, (e, n) in hugin_entries().items():
        ours = name in pozo.WELLS
        ax.plot((e - x0) / KM, (n - y0) / KM, 'o', ms=6 if ours else 4.5, color=HIGHLIGHT if ours else INK,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4)
        if not ours:
            ax.annotate(name, ((e - x0) / KM, (n - y0) / KM), xytext=(4, 4), textcoords='offset points',
                        fontsize=7.5, color=INK, zorder=5)
    for well, offset in (('F-12', (-10, -16)), ('F-11 B', (8, 10))):
        p = path_in_reservoir(well)
        ax.plot((p[:, 2] - x0) / KM, (p[:, 3] - y0) / KM, color=HIGHLIGHT, linewidth=2.4, zorder=3)
        ax.annotate(well, ((p[-1, 2] - x0) / KM, (p[-1, 3] - y0) / KM), xytext=offset, textcoords='offset points',
                    fontsize=11, color=INK, fontweight='bold', zorder=5,
                    bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 1.5, 'alpha': 0.85})
    ax.set_xlim(0, 4.2)
    ax.set_ylim(0, 3.4)
    ax.set_aspect('equal')
    ax.set_xlabel('Este (km)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Norte (km)', fontsize=11, color=SECONDARY)
    bar = fig.colorbar(filled, ax=ax, shrink=0.8, pad=0.02)
    bar.set_label('Tope de la Formación Hugin (m TVDSS)', fontsize=10, color=SECONDARY)
    bar.ax.invert_yaxis()
    bar.ax.tick_params(colors=MUTED, labelsize=9, length=0)
    bar.outline.set_visible(False)
    fig.suptitle('Dónde están los pozos: tope del Hugin y entrada de cada pozo al reservorio',
                 x=0.08, y=0.96, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def figure_sections(surface: np.ndarray, path: Path) -> None:
    """Each well against horizontal distance, coloured by its log Sw, over the mapped top of the Hugin."""
    tree = cKDTree(surface[:, :2])
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), facecolor=SURFACE, sharey=True,
                             gridspec_kw={'width_ratios': [1, 3.2], 'wspace': 0.06, 'left': 0.07,
                                          'right': 0.9, 'top': 0.86, 'bottom': 0.11})
    points = None
    for ax, well in zip(axes, pozo.WELLS):
        _style(ax)
        cells = pozo.load_cells(well)
        step = np.hypot(np.diff(cells.x, prepend=cells.x[0]), np.diff(cells.y, prepend=cells.y[0]))
        distance = np.cumsum(step)
        top = surface[tree.query(np.column_stack([cells.x, cells.y]))[1], 2]
        ax.plot(distance, top, color=SECONDARY, linewidth=1.3, linestyle=(0, (4, 3)))
        ax.plot(distance, cells.tvdss, color=AXIS, linewidth=0.8, zorder=2)
        points = ax.scatter(distance, cells.tvdss, c=cells.sw, cmap=BLUES, vmin=0, vmax=1, s=16,
                            linewidths=0, zorder=3)
        ax.set_xlabel('Distancia horizontal (m)', fontsize=10, color=SECONDARY)
        ax.set_title(f'{well} · {pozo.WELLS[well].logged}', fontsize=12, color=INK, loc='left')
    axes[0].text(0.04, 0.045, 'Tope del Hugin según el mapa', fontsize=9, color=SECONDARY,
                 transform=axes[0].transAxes)
    axes[0].plot([0.04, 0.2], [0.03, 0.03], color=SECONDARY, linewidth=1.3, linestyle=(0, (4, 3)),
                 transform=axes[0].transAxes)
    axes[0].invert_yaxis()
    axes[0].set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    bar = fig.colorbar(points, ax=axes, shrink=0.8, pad=0.015)
    bar.set_label('Sw del perfil (fracción)', fontsize=10, color=SECONDARY)
    bar.ax.tick_params(colors=MUTED, labelsize=9, length=0)
    bar.outline.set_visible(False)
    fig.suptitle('Los dos pozos en sección: trayectoria coloreada por la saturación de agua del perfil',
                 x=0.07, y=0.965, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def monthly_production() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Field totals per month from the operator's file, in thousand Sm3."""
    book = openpyxl.load_workbook(pozo.DATA / 'produccion' / 'Volve production data.xlsx', read_only=True)
    totals: dict[tuple[int, int], list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for row in list(book['Monthly Production Data'].iter_rows(values_only=True))[2:]:
        if row[2] is None:
            continue
        for i, column in enumerate((5, 7, 9)):   # Oil, Water, WI
            if isinstance(row[column], (int, float)):
                totals[(int(row[2]), int(row[3]))][i] += row[column]
    months = sorted(totals)
    when = np.array([y + (m - 0.5) / 12 for y, m in months])
    values = np.array([totals[k] for k in months]) / 1000.0
    return when, dict(zip(SERIES, values.T))


def figure_production(path: Path) -> None:
    when, series = monthly_production()
    fig, ax = plt.subplots(figsize=(10.5, 4.8), facecolor=SURFACE)
    fig.subplots_adjust(left=0.08, right=0.82, top=0.86, bottom=0.12)
    _style(ax)
    for name, values in series.items():
        ax.plot(when, values, color=SERIES[name], linewidth=2)
    # Direct labels at the right edge, spread so they do not overprint where the curves converge.
    ends = sorted(series, key=lambda name: series[name][-1])
    for rank, name in enumerate(ends):
        y = max(series[name][-1], 15 + 32 * rank)
        ax.annotate(name, (when[-1], series[name][-1]), xytext=(when[-1] + 0.25, y), textcoords='data',
                    fontsize=10, color=INK, va='center',
                    arrowprops={'arrowstyle': '-', 'color': SERIES[name], 'linewidth': 1.5})
    ax.set_ylim(0)
    ax.set_xlim(2008, 2016.95)
    ax.set_ylabel('Miles de Sm³ por mes', fontsize=11, color=SECONDARY)
    for year, label in ((2007.65, 'F-12 se perfila'), (2013.45, 'F-11 B se perfila')):
        if year >= 2008:
            ax.axvline(year, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
            ax.text(year + 0.06, ax.get_ylim()[1] * 0.96, label, fontsize=10, color=SECONDARY, va='top')
    fig.suptitle('Producción e inyección mensual del campo, según el archivo del operador',
                 x=0.08, y=0.95, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'slides' / 'img'
    out.mkdir(parents=True, exist_ok=True)
    surface = hugin_map()
    figure_map(surface, out / 'mapa-hugin.png')
    figure_sections(surface, out / 'secciones.png')
    figure_production(out / 'produccion.png')
    cells = pozo.load_all()
    log_only(cells, 'F-12', out / 'perfil-f12.png')
    log_only(cells, 'F-11 B', out / 'perfil-f11b.png')
    when, series = monthly_production()
    print({k: round(float(v.sum()) / 1000, 2) for k, v in series.items()}, 'millones de Sm3')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
