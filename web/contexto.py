"""Context figures for the public page and the first blocks of the class.

    uv run web/contexto.py [output_dir]      default: slides/img

Everything is drawn from the pinned Volve files in datos/volve/. Published numbers that are not
in those files (the DST pressure of 15/9-19 A, the contacts of the operator's report and of the
field deck) are constants below, each with its source.
"""
from __future__ import annotations

import json
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
from sw.graficar import AXIS, GRID, INK, LOG, MUTED, SECONDARY, SURFACE, WELL_COLOR, _style  # noqa: E402
from sw.modelo import OIL_DENSITY, WATER_DENSITY  # noqa: E402

# One hue, light to dark: shallow to deep on the maps, oil to water on the wells.
BLUES = LinearSegmentedColormap.from_list('blues', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
GREENS = LinearSegmentedColormap.from_list('greens', ['#e3f4ec', '#9fd9bf', '#4bb98b', '#147a5f', '#0a4a3a'])
# The colours an engineer expects: oil green, produced water blue, injected water light blue.
SERIES = {'Petróleo': '#008300', 'Agua producida': '#2a78d6', 'Agua inyectada': '#86b6ef'}
WATER, OIL_INK = '#2a78d6', '#147a5f'
KM = 1000.0
X0, Y0 = 433500.0, 6476900.0   # map origin, UTM 31N ED50

# Statoil doc. 3781-06 (2006), table 11: irreducible water of the Volve Hugin.
SWIRR_AT_1MD, SWIRR_SLOPE = 0.45, -0.105
# Same report, table 10: free water level from J-function modelling, m TVDSS.
FWL_REPORT, FWL_REPORT_ERROR = 3120.0, 15.0
# Field deck (VOLVE_2016.DATA), EQUIL of the main structure, m TVDSS.
FWL_DECK = 3200.0
# 15/9-19 A, DST 2A (Final Well Report, table 3.2, on Sodir): 336.5 +/- 0.5 bar, perforations
# at 3,099.9 to 3,102.5 m TVD RT; the rotary table is 25 m above sea level.
DST_19A = (3101.2 - 25.0, 336.5, 0.5)
# 15/9-F-4, MDT oil sample (ResLab 2008): 332.8 bar at 2,928.7 m TVD MSL.
MDT_F4 = (2928.7, 332.8)
BAR_PER_M = 9.80665 / 1e5


def swirr(k: np.ndarray) -> np.ndarray:
    return np.clip(SWIRR_AT_1MD + SWIRR_SLOPE * np.log10(np.maximum(k, 1e-4)), 0.02, 0.90)


def surface(name: str) -> dict[tuple[int, int], tuple[float, float, float]]:
    """A mapped horizon by (inline, crossline): easting, northing, depth in m TVDSS."""
    a = np.loadtxt(pozo.DATA / 'mapas' / name, delimiter=',', skiprows=1)
    return {(int(il), int(xl)): (x, y, z) for il, xl, x, y, z in a}


def as_array(s: dict) -> np.ndarray:
    return np.array(list(s.values()))


def hugin_entries() -> dict[str, tuple[float, float]]:
    """Where each well with a pick first enters the Hugin: short name -> (easting, northing)."""
    out: dict[str, tuple[float, float]] = {}
    for line in (pozo.DATA / 'topes' / 'Well_picks_Volve_v1.dat').read_text(errors='replace').splitlines():
        name = line[2:26].strip().removeprefix('NO 15/9-')
        if line[27:67].strip() != pozo.HUGIN_TOP or name in out:
            continue
        fields = line[78:].split()
        try:
            out[name] = (float(fields[-3]), float(fields[-2]))
        except (ValueError, IndexError):
            continue
    return out


def _map_axes(ax, title: str) -> None:
    _style(ax)
    ax.grid(False)
    ax.set_xlim(0, 4.2)
    ax.set_ylim(0, 3.4)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=11, color=INK, loc='left')


def _wells_on_map(ax, labels: bool, others: bool = True) -> None:
    for name, (e, n) in hugin_entries().items():
        if name in pozo.WELLS or not others:
            continue
        ax.plot((e - X0) / KM, (n - Y0) / KM, 'o', ms=3.5, color=INK, markeredgecolor=SURFACE, markeredgewidth=0.8, zorder=4)
        if labels:
            ax.annotate(name, ((e - X0) / KM, (n - Y0) / KM), xytext=(4, 3), textcoords='offset points',
                        fontsize=7, color=INK, zorder=5)
    for well in pozo.WELLS:
        c = pozo.load_cells(well)
        ax.plot((c.x - X0) / KM, (c.y - Y0) / KM, color=WELL_COLOR[well], linewidth=2.6, zorder=6,
                solid_capstyle='round', path_effects=None)
        ax.plot((c.x[0] - X0) / KM, (c.y[0] - Y0) / KM, 'o', ms=6.5, color=WELL_COLOR[well],
                markeredgecolor=SURFACE, markeredgewidth=1.3, zorder=7)
        if labels:
            ax.annotate(well, ((c.x[0] - X0) / KM, (c.y[0] - Y0) / KM), xytext=(6, 6), textcoords='offset points',
                        fontsize=10, color=INK, fontweight='bold', zorder=8,
                        bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 1.2, 'alpha': 0.85})


def _colorbar(fig, mappable, ax, label: str, invert: bool) -> None:
    bar = fig.colorbar(mappable, ax=ax, shrink=0.82, pad=0.02)
    bar.set_label(label, fontsize=9, color=SECONDARY)
    if invert:
        bar.ax.invert_yaxis()
    bar.ax.tick_params(colors=MUTED, labelsize=8, length=0)
    bar.outline.set_visible(False)


def figure_map(top: dict, path: Path) -> None:
    a = as_array(top)
    fig, ax = plt.subplots(figsize=(9.6, 7.2), facecolor=SURFACE)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    _map_axes(ax, '')
    filled = ax.tricontourf((a[:, 0] - X0) / KM, (a[:, 1] - Y0) / KM, a[:, 2], levels=np.arange(2700, 3401, 50), cmap=BLUES)
    _wells_on_map(ax, labels=True)
    ax.set_xlabel('Este (km)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Norte (km)', fontsize=11, color=SECONDARY)
    _colorbar(fig, filled, ax, 'Tope de la Formación Hugin (m TVDSS)', invert=True)
    fig.suptitle('Tope del Hugin y los seis pozos del ejercicio, con su tramo dentro del Hugin',
                 x=0.08, y=0.96, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def figure_surfaces(top: dict, base: dict, bcu: dict, path: Path) -> None:
    """Three mapped horizons on one depth scale, and the thickness of the Hugin between two of them."""
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.4), facecolor=SURFACE)
    fig.subplots_adjust(left=0.05, right=0.97, top=0.91, bottom=0.06, wspace=0.08, hspace=0.16)
    levels = np.arange(2600, 3451, 50)
    for ax, (s, title) in zip(axes.flat, ((bcu, 'Discordancia de la base del Cretácico (BCU)'),
                                          (top, 'Tope de la Formación Hugin'), (base, 'Base de la Formación Hugin'))):
        a = as_array(s)
        _map_axes(ax, title)
        filled = ax.tricontourf((a[:, 0] - X0) / KM, (a[:, 1] - Y0) / KM, a[:, 2], levels=levels, cmap=BLUES, extend='both')
        _wells_on_map(ax, labels=False, others=False)
        _colorbar(fig, filled, ax, 'm TVDSS', invert=True)
    common = [k for k in top if k in base]
    xyz = np.array([(top[k][0], top[k][1], base[k][2] - top[k][2]) for k in common])
    ax = axes[1, 1]
    _map_axes(ax, 'Espesor del Hugin: base menos tope')
    filled = ax.tricontourf((xyz[:, 0] - X0) / KM, (xyz[:, 1] - Y0) / KM, np.clip(xyz[:, 2], 0, None),
                            levels=np.arange(0, 201, 20), cmap=GREENS, extend='max')
    _wells_on_map(ax, labels=True, others=False)
    _colorbar(fig, filled, ax, 'm', invert=False)
    fig.suptitle('Las superficies mapeadas del conjunto: tres horizontes y el espesor del reservorio',
                 x=0.05, y=0.965, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=120, facecolor=SURFACE)
    plt.close(fig)


def figure_sections(top: dict, base: dict, bcu: dict, path: Path) -> None:
    """Each well against horizontal distance, coloured by its log Sw, between the mapped horizons."""
    trees = {}
    for name, s in (('BCU', bcu), ('Tope del Hugin', top), ('Base del Hugin', base)):
        a = as_array(s)
        trees[name] = (cKDTree(a[:, :2]), a[:, 2])
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.6), facecolor=SURFACE, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.9, top=0.88, bottom=0.08, wspace=0.08, hspace=0.3)
    points = None
    for ax, well in zip(axes.flat, pozo.WELLS):
        _style(ax)
        spec = pozo.WELLS[well]
        intervals = pozo.hugin_intervals(spec.picks_name)
        md = np.arange(intervals[0][0] - 60, intervals[-1][1] + 40, 2.0)
        z, x, y = pozo.position(well, md)
        distance = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
        for (name, (tree, depth)), style in zip(trees.items(), ((0, (1, 2)), (0, (5, 2)), '-')):
            ax.plot(distance, depth[tree.query(np.column_stack([x, y]))[1]], color=SECONDARY, linewidth=1.1,
                    linestyle=style, label=name)
        ax.plot(distance, z, color=AXIS, linewidth=1.0, zorder=2)
        cells = pozo.load_cells(well)
        points = ax.scatter(np.interp(cells.md, md, distance), cells.tvdss, c=cells.sw, cmap=BLUES, vmin=0, vmax=1,
                            s=14, linewidths=0, zorder=3)
        ax.set_title(f'{well} · {spec.logged}' + (' · control' if spec.role == 'control' else ''),
                     fontsize=11, color=INK, loc='left')
        ax.set_xlabel('Distancia horizontal (m)', fontsize=9, color=SECONDARY)
    axes[0, 0].invert_yaxis()
    axes[0, 0].set_ylim(3320, 2760)
    for ax in axes[:, 0]:
        ax.set_ylabel('Profundidad (m TVDSS)', fontsize=10, color=SECONDARY)
    axes[0, 0].legend(loc='lower left', frameon=False, fontsize=8, labelcolor=SECONDARY)
    bar = fig.colorbar(points, ax=axes, shrink=0.7, pad=0.015)
    bar.set_label('Sw del perfil en el Hugin (fracción)', fontsize=10, color=SECONDARY)
    bar.ax.tick_params(colors=MUTED, labelsize=9, length=0)
    bar.outline.set_visible(False)
    fig.suptitle('Los seis pozos en sección, entre los horizontes del mapa: claro es petróleo, oscuro es agua',
                 x=0.07, y=0.96, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=125, facecolor=SURFACE)
    plt.close(fig)


def figure_quicklook(well: str, raw_file: str | None, path: Path) -> None:
    """The reading an analyst does first: where the sand is, how porous, how much water, and how
    much of that water is held by the rock."""
    spec = pozo.WELLS[well]
    log = pozo.load_log(well)
    top, base = pozo.hugin_intervals(spec.picks_name)[0]
    pad = 12.0
    m = (log['md'] >= top - pad) & (log['md'] <= base + pad)
    depth, phi, sw, k, vsh, net = (log[key][m] for key in ('tvdss', 'phi', 'sw', 'k', 'vsh', 'net'))
    hold = swirr(k)
    tracks = ['arena'] + (['rt', 'dn'] if raw_file else []) + ['phi', 'sw', 'bvw']
    fig, axes = plt.subplots(1, len(tracks), figsize=(2.15 * len(tracks) + 0.6, 7.0), sharey=True, facecolor=SURFACE)
    fig.subplots_adjust(left=0.085 if raw_file else 0.11, right=0.985, top=0.83, bottom=0.13, wspace=0.12)
    raw = pozo.read_curves(raw_file) if raw_file else None
    if raw:
        rm = (raw['MD'] >= top - pad) & (raw['MD'] <= base + pad)
        rdepth = pozo.position(well, raw['MD'][rm])[0]
    z_top, z_base = pozo.position(well, np.array([top, base]))[0]
    for ax, track in zip(axes, tracks):
        _style(ax)
        for z in (z_top, z_base):
            ax.axhline(z, color=SECONDARY, linewidth=0.8)
        if track == 'arena':
            if raw:
                ax.plot(raw['GR'][rm], rdepth, color=INK, linewidth=0.9)
                ax.set_xlim(0, 150)
                label = 'Rayos gamma (API)'
            else:
                ax.plot(vsh, depth, color=INK, linewidth=0.9)
                ax.set_xlim(0, 1)
                label = 'Volumen de arcilla (fracción)'
            ax.fill_betweenx(depth, *ax.get_xlim(), where=net, color='#f3d27a', alpha=0.55, linewidth=0, step='mid')
            ax.set_title(f'Arena neta\n{label}', fontsize=9, color=INK, loc='left')
        elif track == 'rt':
            ax.plot(raw['RT'][rm], rdepth, color=INK, linewidth=0.9)
            ax.set_xscale('log')
            ax.set_xlim(0.2, 2000)
            ax.set_title('Resistividad\nRT (ohm·m)', fontsize=9, color=INK, loc='left')
        elif track == 'dn':
            # The log analyst's overlay: both curves read as limestone porosity on one scale.
            dphi = (2.71 - raw['RHOB'][rm]) / (2.71 - 1.0)
            ax.plot(raw['NPHI'][rm], rdepth, color=WATER, linewidth=0.9, label='Neutrón')
            ax.plot(dphi, rdepth, color=INK, linewidth=0.9, label='Densidad')
            ax.set_xlim(0.45, -0.15)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.045), frameon=False, fontsize=8, labelcolor=SECONDARY, ncols=2,
                      handlelength=1.2, columnspacing=0.8)
            ax.set_xticks([0.4, 0.2, 0.0])
            ax.set_title('Densidad y neutrón\nporosidad caliza (fracción)', fontsize=9, color=INK, loc='left')
        elif track == 'phi':
            ax.fill_betweenx(depth, 0, phi, color=GRID, linewidth=0)
            ax.plot(phi, depth, color=INK, linewidth=0.9)
            ax.set_xlim(0.35, 0)
            ax.set_xticks([0.3, 0.2, 0.1, 0])
            ax.set_title('Porosidad\nPHIF (fracción)', fontsize=9, color=INK, loc='left')
        elif track == 'sw':
            ax.plot(sw, depth, color=WATER, linewidth=1.1, label='Sw')
            ax.plot(hold, depth, color=INK, linewidth=0.8, linestyle=(0, (3, 2)), label='Swirr')
            ax.set_xlim(1, 0)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.045), frameon=False, fontsize=8, labelcolor=SECONDARY, ncols=2,
                      handlelength=1.2, columnspacing=0.8)
            ax.set_xticks([1, 0.5, 0])
            ax.set_xticklabels(['1', '0.5', '0'])
            ax.set_title('Saturación de agua\nSw y Swirr (fracción)', fontsize=9, color=INK, loc='left')
        else:
            bound = phi * np.minimum(sw, hold)
            ax.fill_betweenx(depth, 0, bound, color='#9ec5f4', linewidth=0, label='Agua irreducible')
            ax.fill_betweenx(depth, bound, phi * sw, color='#1c5cab', linewidth=0, label='Agua móvil')
            ax.fill_betweenx(depth, phi * sw, phi, color='#d9ecd9', linewidth=0, label='Hidrocarburo')
            ax.set_xlim(0.35, 0)
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.045), frameon=False, fontsize=8, labelcolor=SECONDARY, ncols=1,
                      handlelength=1.2)
            ax.set_xticks([0.3, 0.2, 0.1, 0])
            ax.set_title('Volumen de fluidos\nBVW = PHIF · Sw (fracción)', fontsize=9, color=INK, loc='left')
    axes[0].set_ylim(depth.max(), depth.min())
    axes[0].set_ylabel('Profundidad (m TVDSS)', fontsize=10, color=SECONDARY)
    for z, label in ((z_top, 'tope del Hugin'), (z_base, 'base del Hugin')):
        axes[0].text(0.03, z, label, fontsize=8, color=SECONDARY, va='bottom', ha='left',
                     transform=axes[0].get_yaxis_transform())
    mobile = float(np.mean((sw[net] - hold[net]) > 0.05)) if net.any() else 0.0
    fig.suptitle(f'15/9-{well}, perfilado en {spec.logged}: lectura rápida del Hugin',
                 x=0.085 if raw_file else 0.11, y=0.975, ha='left', fontsize=13, color=INK)
    fig.text(0.085 if raw_file else 0.11, 0.925,
             f'Fondo amarillo: arena neta. Swirr = 0.45 − 0.105 · log k (operador). '
             f'Agua móvil (Sw más de 0.05 sobre Swirr) en el {mobile:.0%} de la arena.',
             fontsize=9, color=SECONDARY)
    fig.savefig(path, dpi=125, facecolor=SURFACE)
    plt.close(fig)


def figure_buckles(path: Path) -> None:
    """Porosity against water saturation: cells on a line of constant BVW hold only irreducible water."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), facecolor=SURFACE,
                             gridspec_kw={'left': 0.07, 'right': 0.98, 'top': 0.84, 'bottom': 0.12, 'wspace': 0.2})
    ax = axes[0]
    _style(ax)
    for well in pozo.FIT_WELLS:
        c = pozo.load_cells(well)
        ax.scatter(c.sw[c.net], c.phi[c.net], s=10, color=WELL_COLOR[well], alpha=0.6, linewidths=0, label=well)
    s = np.linspace(0.03, 1, 200)
    for bvw in (0.02, 0.04, 0.08):
        ax.plot(s, bvw / s, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.text(bvw / 0.112 + 0.012, 0.112, f'BVW {bvw:.2f}', fontsize=8, color=SECONDARY, ha='left',
                bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 1})
    ax.set_xlim(0, 1)
    ax.set_ylim(0.08, 0.35)
    ax.set_xlabel('Sw (fracción)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Porosidad (fracción)', fontsize=11, color=SECONDARY)
    ax.legend(loc='lower right', frameon=False, fontsize=9, labelcolor=SECONDARY, markerscale=2)
    ax.set_title('Buckles: porosidad contra saturación, arena neta', fontsize=11, color=INK, loc='left')

    ax = axes[1]
    _style(ax)
    for well in pozo.FIT_WELLS:
        c = pozo.load_cells(well)
        ax.scatter(c.k[c.net], c.sw[c.net], s=10, color=WELL_COLOR[well], alpha=0.6, linewidths=0)
    k = np.geomspace(0.1, 2e4, 100)
    ax.plot(k, swirr(k), color=INK, linewidth=1.6)
    ax.text(0.5, swirr(np.array([0.5]))[0] + 0.05, 'Swirr del operador', fontsize=9, color=INK, ha='left',
            bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 1})
    ax.set_xscale('log')
    ax.set_xlim(0.1, 2e4)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Permeabilidad (mD)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Sw (fracción)', fontsize=11, color=SECONDARY)
    ax.set_title('Sw contra permeabilidad: sobre la línea, agua móvil', fontsize=11, color=INK, loc='left')
    fig.suptitle('¿Cuánta del agua es irreducible? Los cinco pozos perfilados antes de producir',
                 x=0.07, y=0.96, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=125, facecolor=SURFACE)
    plt.close(fig)


def pressure_points() -> tuple[np.ndarray, np.ndarray]:
    """Valid formation pressures of 15/9-19 BT2 (1998): depth in m TVDSS, pressure in bar."""
    record = json.loads((pozo.DATA / 'presiones' / 'L916RFT_19BT2.json').read_text())[0]
    names = [c['name'] for c in record['curves']]
    rows = np.array([[np.nan if v is None else v for v in row] for row in record['data']], dtype=float)
    md, p, quality = rows[:, 0], rows[:, names.index('PFOR')], rows[:, names.index('QUAL')]
    ok = np.isfinite(p) & (p > 0) & (quality >= 3)
    return pozo.position('19 BT2', md[ok])[0], p[ok]


def figure_pressure(path: Path) -> dict[str, float]:
    depth, p = pressure_points()
    hugin = depth > 3100
    slope, intercept = np.polyfit(depth[hugin], p[hugin], 1)
    oil_gradient = OIL_DENSITY * BAR_PER_M
    z_dst, p_dst, dp = DST_19A
    # Depth where the oil line through the DST point meets the water line.
    fwl = (p_dst - oil_gradient * z_dst - intercept) / (slope - oil_gradient)
    spread = dp / (slope - oil_gradient)

    fig, ax = plt.subplots(figsize=(9.2, 6.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.1)
    _style(ax)
    z = np.array([2800.0, 3300.0])
    ax.axhspan(FWL_REPORT - FWL_REPORT_ERROR, FWL_REPORT + FWL_REPORT_ERROR, color=GRID, alpha=0.8, linewidth=0)
    ax.text(318.3, FWL_REPORT - 2, f'Informe 2006: FWL {FWL_REPORT:,.0f} ± {FWL_REPORT_ERROR:.0f} m (por función J)',
            fontsize=9, color=SECONDARY, va='center')
    ax.axhline(FWL_DECK, color=SECONDARY, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(318.3, FWL_DECK - 5, f'Modelo de campo: contacto {FWL_DECK:,.0f} m', fontsize=9, color=SECONDARY)
    ax.plot(intercept + slope * z, z, color=WATER, linewidth=1.3)
    ax.plot(p_dst + oil_gradient * (z - z_dst), z, color=OIL_INK, linewidth=1.3)
    ax.plot(p[hugin], depth[hugin], 'o', ms=6, color=WELL_COLOR['19 BT2'], markeredgecolor=SURFACE, markeredgewidth=1,
            label=f'19 BT2, probador de formación (1998): {hugin.sum()} puntos en agua')
    ax.errorbar([p_dst], [z_dst], xerr=[dp], fmt='o', ms=7, color=WELL_COLOR['19 A'], markeredgecolor=SURFACE,
                ecolor=WELL_COLOR['19 A'], capsize=3, label='19 A, ensayo de formación (1997): 336.5 ± 0.5 bar')
    ax.plot([MDT_F4[1]], [MDT_F4[0]], 's', ms=7, color=WELL_COLOR['F-4'], markeredgecolor=SURFACE,
            label='F-4, muestra de petróleo (febrero de 2008): 332.8 bar')
    ax.plot([intercept + slope * fwl], [fwl], 'D', ms=7, color=INK, zorder=5)
    ax.annotate(f'Cruce: {fwl:,.0f} ± {abs(spread):.0f} m', (intercept + slope * fwl, fwl), xytext=(10, -4),
                textcoords='offset points', fontsize=10, color=INK, va='top')
    ax.text(intercept + slope * 2990 - 0.6, 2990, f'agua: {slope:.4f} bar/m\n({slope / BAR_PER_M:,.0f} kg/m³)', fontsize=9,
            color=WATER, va='center', ha='right')
    ax.text(p_dst + oil_gradient * (2850 - z_dst) + 0.6, 2850, f'petróleo: {oil_gradient:.4f} bar/m\n({OIL_DENSITY:.0f} kg/m³)',
            fontsize=9, color=OIL_INK, va='center')
    ax.set_xlim(318, 356)
    ax.set_ylim(3300, 2800)
    ax.set_xlabel('Presión de formación (bar)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    ax.legend(loc='upper right', frameon=False, fontsize=9, labelcolor=SECONDARY)
    fig.suptitle('Presiones previas a la producción: tres fuentes y tres contactos', x=0.1, y=0.955, ha='left',
                 fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    return {'gradiente_agua_bar_m': float(slope), 'densidad_agua_equivalente': float(slope / BAR_PER_M),
            'gradiente_petroleo_bar_m': float(oil_gradient), 'cruce_m': float(fwl), 'cruce_error_m': float(abs(spread)),
            'mdt_f4_sobre_linea_petroleo_bar': float(MDT_F4[1] - (p_dst + oil_gradient * (MDT_F4[0] - z_dst))),
            'densidad_agua_modelo': WATER_DENSITY}


def figure_sw_depth(path: Path) -> None:
    """Every net cell of the five fitted wells on one depth axis: the transition is in the data."""
    fig, ax = plt.subplots(figsize=(8.6, 6.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.88, bottom=0.1)
    _style(ax)
    for well in pozo.FIT_WELLS:
        c = pozo.load_cells(well)
        ax.scatter(c.sw[c.net], c.tvdss[c.net], s=11, color=WELL_COLOR[well], alpha=0.65, linewidths=0,
                   label=f'{well} ({pozo.WELLS[well].logged.split()[-1]})')
    ax.axhspan(FWL_REPORT - FWL_REPORT_ERROR, FWL_REPORT + FWL_REPORT_ERROR, color=GRID, alpha=0.8, linewidth=0)
    ax.text(0.98, FWL_REPORT, 'FWL del informe', fontsize=9, color=SECONDARY, ha='right', va='center')
    ax.axhline(FWL_DECK, color=SECONDARY, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(0.02, FWL_DECK - 4, 'contacto del modelo de campo', fontsize=9, color=SECONDARY)
    ax.set_xlim(0, 1)
    ax.set_ylim(3290, 2800)
    ax.set_xlabel('Sw del perfil (fracción)', fontsize=11, color=SECONDARY)
    ax.set_ylabel('Profundidad (m TVDSS)', fontsize=11, color=SECONDARY)
    ax.legend(loc='lower left', frameon=False, fontsize=9, labelcolor=SECONDARY, markerscale=2)
    fig.suptitle('Lo que hay que reproducir: Sw de la arena neta del Hugin\nen los cinco pozos perfilados antes de producir',
                 x=0.11, y=0.97, ha='left', fontsize=13, color=INK)
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
    ax.set_xlim(2007.9, 2016.95)
    ax.set_ylabel('Miles de Sm³ por mes', fontsize=11, color=SECONDARY)
    top = ax.get_ylim()[1]
    for year, label, y in ((2008.12, 'Primer petróleo: los cinco\npozos de ajuste ya están perfilados', 0.97),
                           (2013.45, 'Se perfila F-11 B,\nel pozo de control', 0.97)):
        ax.axvline(year, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.text(year + 0.07, top * y, label, fontsize=9.5, color=SECONDARY, va='top', zorder=5,
                bbox={'facecolor': SURFACE, 'edgecolor': 'none', 'pad': 2, 'alpha': 0.85})
    fig.suptitle('Producción e inyección mensual del campo, según el archivo del operador',
                 x=0.08, y=0.95, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def figure_j_review(path: Path) -> None:
    """What the J function buys: one curve instead of one capillary pressure curve per rock."""
    a, b = 2.222, 1.111                      # Statoil 3781-06, table 11: Swn = a * J^-b
    rocks = ((10.0, 0.17, '#0d366b'), (100.0, 0.20, '#3987e5'), (1000.0, 0.23, '#86b6ef'))
    height = np.geomspace(0.5, 400, 300)
    pc = (WATER_DENSITY - OIL_DENSITY) * BAR_PER_M * height
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), facecolor=SURFACE,
                             gridspec_kw={'left': 0.07, 'right': 0.98, 'top': 0.82, 'bottom': 0.13, 'wspace': 0.22})
    for k, phi, color in rocks:
        j = pc * np.sqrt(k / phi) / (2.0 * 0.318316)
        swn = np.minimum(1.0, a * j ** -b)
        hold = swirr(np.array([k]))[0]
        sw = hold + (1 - hold) * swn
        axes[0].plot(sw, height, color=color, linewidth=2, label=f'{k:,.0f} mD, porosidad {phi:.2f}')
        axes[1].plot(swn, j, color=color, linewidth=5 if k == 10 else 3 if k == 100 else 1.4)
    for ax in axes:
        _style(ax)
    axes[0].set_xlim(0, 1)
    axes[0].set_yscale('log')
    axes[0].set_ylim(0.5, 400)
    axes[0].legend(loc='upper right', frameon=False, fontsize=9.5, labelcolor=SECONDARY)
    axes[0].set_xlabel('Sw (fracción)', fontsize=11, color=SECONDARY)
    axes[0].set_ylabel('Altura sobre el nivel de agua libre (m)', fontsize=11, color=SECONDARY)
    axes[0].set_title('Tres rocas, tres perfiles de saturación', fontsize=11, color=INK, loc='left')
    axes[1].set_yscale('log')
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(1, 1e5)
    axes[1].set_xlabel('Sw normalizada: (Sw − Swirr) / (1 − Swirr)', fontsize=11, color=SECONDARY)
    axes[1].set_ylabel('J', fontsize=11, color=SECONDARY, rotation=0, labelpad=10)
    axes[1].set_title('Las mismas tres rocas, una sola curva', fontsize=11, color=INK, loc='left')
    fig.suptitle('Qué hace la función J: saca la roca de la curva', x=0.07, y=0.96, ha='left', fontsize=13, color=INK)
    fig.text(0.07, 0.895, 'Con las constantes del informe del operador (2006): Swn = 2.222 · J^−1.111, '
             'Swirr = 0.45 − 0.105 · log k, σ·cosθ = 2 mN/m.', fontsize=9.5, color=SECONDARY)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def figure_tilt(path: Path) -> None:
    """Fit and control error against the tilt of the free water level, from the optimizer scan."""
    table = np.loadtxt(Path(__file__).resolve().parent.parent / 'docente' / 'plan-b' / 'barrido_inclinacion.tsv',
                       skiprows=1)
    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor=SURFACE)
    fig.subplots_adjust(left=0.09, right=0.8, top=0.84, bottom=0.14)
    _style(ax)
    series = (('Ajuste, 5 pozos', 2, INK, 2.2), ('F-4', 3, WELL_COLOR['F-4'], 1.6), ('19 A', 4, WELL_COLOR['19 A'], 1.6),
              ('Control, F-11 B', 5, WELL_COLOR['F-11 B'], 1.6))
    ends = sorted(series, key=lambda s: table[-1, s[1]])
    for name, column, color, width in series:
        ax.plot(table[:, 0], table[:, column], color=color, linewidth=width, marker='o', ms=5,
                markeredgecolor=SURFACE, markeredgewidth=1)
    for rank, (name, column, color, _) in enumerate(ends):
        ax.annotate(name, (table[-1, 0], table[-1, column]), xytext=(table[-1, 0] + 8, max(table[-1, column], 0.085 + 0.022 * rank)),
                    textcoords='data', fontsize=10, color=INK, va='center',
                    arrowprops={'arrowstyle': '-', 'color': color, 'linewidth': 1.3})
    ax.axvline(0, color=SECONDARY, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.text(1.5, ax.get_ylim()[1] * 0.985, 'contacto plano', fontsize=9, color=SECONDARY, va='top')
    ax.set_ylim(0)
    ax.set_xlabel('Inclinación del nivel de agua libre de 19 A hacia F-4 (m por km; negativo: más somero en F-4)',
                  fontsize=10, color=SECONDARY)
    ax.set_ylabel('RMSE de Sw', fontsize=11, color=SECONDARY)
    fig.suptitle('¿Contacto inclinado? El ajuste mejora, el control no', x=0.09, y=0.95, ha='left', fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def figure_perched(path: Path) -> None:
    """Fit and control error against the local water level under F-4, with the independent estimates."""
    table = np.loadtxt(Path(__file__).resolve().parent.parent / 'docente' / 'plan-b' / 'barrido_agua_colgada.tsv',
                       skiprows=1)
    table = table[table[:, 0] <= 3100]
    fig, ax = plt.subplots(figsize=(9.6, 5.2), facecolor=SURFACE)
    fig.subplots_adjust(left=0.09, right=0.8, top=0.84, bottom=0.14)
    _style(ax)
    ax.axvspan(3016, 3024, color=GRID, alpha=0.9, linewidth=0)
    ax.text(3020, 0.292, 'derrame de\nla cubeta', fontsize=9, color=SECONDARY, ha='center', va='top')
    ax.axvline(3025, color=SECONDARY, linewidth=0.9, linestyle=(0, (2, 2)))
    ax.text(3026, 0.245, 'modelo\nde campo', fontsize=9, color=SECONDARY, va='top')
    ax.axvline(3033.3, color=SECONDARY, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(3034.5, 0.292, 'base del Hugin\nen F-4', fontsize=9, color=SECONDARY, va='top')
    series = (('Ajuste, 5 pozos', 1, INK, 2.2), ('F-4', 2, WELL_COLOR['F-4'], 1.6), ('Control, F-11 B', 4, WELL_COLOR['F-11 B'], 1.6))
    for name, column, color, width in series:
        ax.plot(table[:, 0], table[:, column], color=color, linewidth=width, marker='o', ms=5,
                markeredgecolor=SURFACE, markeredgewidth=1)
        ax.annotate(name, (table[-1, 0], table[-1, column]), xytext=(8, 0), textcoords='offset points',
                    fontsize=10, color=INK, va='center')
    ax.set_ylim(0, 0.3)
    ax.set_xlabel('Nivel de agua libre local bajo F-4 (m TVDSS)', fontsize=10, color=SECONDARY)
    ax.set_ylabel('RMSE de Sw', fontsize=11, color=SECONDARY)
    fig.suptitle('Agua colgada en F-4: el perfil pide un nivel local en 3,033 m', x=0.09, y=0.95, ha='left',
                 fontsize=13, color=INK)
    fig.savefig(path, dpi=130, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'slides' / 'img'
    out.mkdir(parents=True, exist_ok=True)
    top, base, bcu = surface('Hugin_Fm_Top.csv'), surface('Hugin_Fm_Base.csv'), surface('BCU.csv')
    figure_map(top, out / 'mapa-hugin.png')
    figure_surfaces(top, base, bcu, out / 'superficies.png')
    figure_sections(top, base, bcu, out / 'secciones.png')
    figure_production(out / 'produccion.png')
    figure_quicklook('F-12', 'perfiles/15_9-F-12/WLC_PETRO_COMPUTED_INPUT_1.LAS', out / 'quicklook-f12.png')
    figure_quicklook('F-4', 'perfiles/15_9-F-4/WLC_PETRO_COMPUTED_INPUT_1.DLIS', out / 'quicklook-f4.png')
    figure_quicklook('19 A', None, out / 'quicklook-19a.png')
    figure_buckles(out / 'buckles.png')
    figure_sw_depth(out / 'sw-profundidad.png')
    figure_j_review(out / 'repaso-j.png')
    figure_tilt(out / 'inclinacion.png')
    figure_perched(out / 'agua-colgada.png')
    numbers = figure_pressure(out / 'presiones.png')
    (out / 'presiones.json').write_text(json.dumps(numbers, indent=1))
    print(json.dumps(numbers, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
