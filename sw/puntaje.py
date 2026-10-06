"""The fixed metric: how far the initialized water saturation is from the logs.

Nothing in this file is tuned by a case. Only net sand of the Hugin counts. The fit is scored on
the five wells logged before first oil (12 February 2008). Two wells are never shown to a case:

- `control_inicial`, 15/9-F-5: logged in July 2008, with 5% of the field's final oil produced and
  before the well started injecting. It stands for the initial state: a good case predicts it
  about as well as the wells it was fitted to.
- `control_barrido`, 15/9-F-11 B: logged in 2013, with 77% of the final oil produced and 19 million
  Sm3 of water injected. Its water saturation is at least the initial one, so a good case should
  not sit above it: its bias should be zero or negative.
"""
from __future__ import annotations

import numpy as np

from sw.pozo import FIT_WELLS, ROLES, WELLS, Cells


def rmse(sim: np.ndarray, log: np.ndarray) -> float:
    return float(np.sqrt(np.mean((sim - log) ** 2)))


def hcpv_error(cells: Cells, sim: np.ndarray, log: np.ndarray) -> float:
    """Relative error in hydrocarbon pore volume along the hole: (simulated - log) / log."""
    pore = cells.phi * cells.length
    return float((pore * (1.0 - sim)).sum() / (pore * (1.0 - log)).sum() - 1.0)


def score(cells: Cells, sw_sim: np.ndarray, n_parameters: int) -> dict[str, float | int]:
    """`cells` must carry the log saturation of every well, including the control."""
    out: dict[str, float | int] = {}
    for role in ROLES:
        wells = [w.name for w in WELLS.values() if w.role == role]
        m = np.isin(cells.well, wells) & cells.net
        sim, log = sw_sim[m], cells.sw[m]
        out[f'rmse_{role}'] = rmse(sim, log)
        out[f'sesgo_{role}'] = float(np.mean(sim - log))
        out[f'rmse_bvw_{role}'] = rmse(cells.phi[m] * sim, cells.phi[m] * log)
        out[f'error_hcpv_{role}'] = hcpv_error(cells.mask(m), sim, log)
        out[f'n_celdas_{role}'] = int(m.sum())
    for spec in WELLS.values():
        m = cells.of(spec.name) & cells.net
        out[f'rmse_{spec.slug}'] = rmse(sw_sim[m], cells.sw[m])
    out['n_parametros'] = n_parameters
    return out


def block(description: str, result: dict[str, float | int], fwl: list[float], seconds: float) -> str:
    """The summary evaluar.py prints: one `key: value` per line, easy to grep."""
    order = (['rmse_ajuste', 'sesgo_ajuste', 'rmse_bvw_ajuste', 'error_hcpv_ajuste']
             + [f'rmse_{WELLS[w].slug}' for w in FIT_WELLS]
             + ['rmse_control_inicial', 'sesgo_control_inicial', 'error_hcpv_control_inicial',
                'rmse_control_barrido', 'sesgo_control_barrido', 'error_hcpv_control_barrido',
                'n_parametros', 'n_celdas_ajuste', 'n_celdas_control_inicial', 'n_celdas_control_barrido'])
    lines = ['---', f'caso: {description}']
    for key in order:
        v = result[key]
        lines.append(f'{key}: {v:.4f}' if isinstance(v, float) else f'{key}: {v}')
    lines.append('fwl: ' + ' '.join(f'{f:.1f}' for f in sorted(set(fwl))[:6])
                 + (' ...' if len(set(fwl)) > 6 else ''))
    lines.append(f'segundos_flow: {seconds:.1f}')
    return '\n'.join(lines)
