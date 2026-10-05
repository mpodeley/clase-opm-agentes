"""The fixed metric: how far the initialized water saturation is from the log.

Nothing in this file is tuned by the case. The fitted well is F-12, logged in 2007 before
production started. F-11 B is held out; it was logged in 2013, after five years of production
and water injection, so its water saturation is at least the initial one.
"""
from __future__ import annotations

import numpy as np

from sw.pozo import WELLS, Cells


def rmse(sim: np.ndarray, log: np.ndarray) -> float:
    return float(np.sqrt(np.mean((sim - log) ** 2)))


def hcpv_error(cells: Cells, sim: np.ndarray, log: np.ndarray) -> float:
    """Relative error in hydrocarbon pore volume along the hole: (simulated - log) / log."""
    pore = cells.phi * cells.length
    return float((pore * (1.0 - sim)).sum() / (pore * (1.0 - log)).sum() - 1.0)


def score(cells: Cells, sw_sim: np.ndarray, n_parameters: int) -> dict[str, float | int]:
    """`cells` must carry the log saturation of every well, including the held-out one."""
    out: dict[str, float | int] = {}
    for spec in WELLS.values():
        m = cells.of(spec.name)
        sim, log = sw_sim[m], cells.sw[m]
        out[f'rmse_{spec.role}'] = rmse(sim, log)
        out[f'sesgo_{spec.role}'] = float(np.mean(sim - log))
        out[f'error_hcpv_{spec.role}'] = hcpv_error(cells.mask(m), sim, log)
        out[f'n_celdas_{spec.role}'] = int(m.sum())
        if spec.role == 'ajuste':
            hugin = cells.zone[m] == 'Hugin'
            out['rmse_ajuste_hugin'] = rmse(sim[hugin], log[hugin])
            out['rmse_ajuste_bajo_hugin'] = rmse(sim[~hugin], log[~hugin])
    out['n_parametros'] = n_parameters
    return out


ORDER = ['rmse_ajuste', 'rmse_ajuste_hugin', 'rmse_ajuste_bajo_hugin', 'sesgo_ajuste', 'error_hcpv_ajuste',
         'rmse_validacion', 'sesgo_validacion', 'error_hcpv_validacion',
         'n_parametros', 'n_celdas_ajuste', 'n_celdas_validacion']


def block(description: str, result: dict[str, float | int], seconds: float) -> str:
    """The summary evaluar.py prints: one `key: value` per line, easy to grep."""
    lines = ['---', f'caso: {description}']
    for key in ORDER:
        v = result[key]
        lines.append(f'{key}: {v:.4f}' if isinstance(v, float) else f'{key}: {v}')
    lines.append(f'segundos_flow: {seconds:.1f}')
    return '\n'.join(lines)
