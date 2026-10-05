"""Classical optimizer for a reference case: Nelder-Mead over its PARAMS, one Flow run per trial.

    uv run docente/optimizar.py docente/soluciones/caso_b.py
    uv run docente/optimizar.py docente/soluciones/caso_f2.py --ver-validacion

It minimizes the RMSE over the cells whose log the case is allowed to see and prints the
best PARAMS, to paste back into the case file. It is the baseline the agent loop is compared with.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluar import initialize  # noqa: E402
from sw.correr import FlowError  # noqa: E402
from sw.pozo import WELLS, load_all  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('caso', type=Path)
    ap.add_argument('--ver-validacion', action='store_true')
    ap.add_argument('--max-corridas', type=int, default=250)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location('caso', args.caso)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = list(module.PARAMS)
    x0 = np.array([module.PARAMS[n] for n in names], dtype=float)
    scale = np.where(x0 != 0, np.abs(x0), 1.0)

    cells = load_all()
    held_out = [] if args.ver_validacion else [w.name for w in WELLS.values() if w.role == 'validacion']
    visible = cells.hide_sw(held_out)
    target = np.isfinite(visible.sw)
    runs, t0 = 0, time.monotonic()

    with tempfile.TemporaryDirectory() as tmp:
        def objective(u: np.ndarray) -> float:
            nonlocal runs
            runs += 1
            p = dict(zip(names, u * scale))
            try:
                case = module.build(visible, p).resolved(len(cells))
                sw_sim, _ = initialize(case, cells, Path(tmp))
            except (ValueError, FlowError):
                return 1.0   # out of range: worse than any real case
            return float(np.sqrt(np.mean((sw_sim[target] - cells.sw[target]) ** 2)))

        start = objective(x0 / scale)
        best = minimize(objective, x0 / scale, method='Nelder-Mead',
                        options={'maxfev': args.max_corridas, 'xatol': 1e-3, 'fatol': 1e-5})

    print(f'corridas: {runs}   segundos: {time.monotonic() - t0:.0f}')
    print(f'rmse inicial: {start:.4f}   rmse final: {best.fun:.4f}')
    print('PARAMS = {' + ', '.join(f"'{n}': {v:.4g}" for n, v in zip(names, best.x * scale)) + '}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
