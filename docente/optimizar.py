"""Classical optimizer for a reference case: Nelder-Mead over its PARAMS, one Flow run per trial.

    uv run docente/optimizar.py docente/soluciones/caso_j1.py

It minimizes `rmse_ajuste`, the same number the agent loop sees, and prints the best PARAMS to
paste back into the case file. It is the baseline the agent loop is compared with.
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
from sw import puntaje  # noqa: E402
from sw.correr import FlowError  # noqa: E402
from sw.pozo import CONTROL_WELLS, load_all  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('caso', type=Path)
    ap.add_argument('--max-corridas', type=int, default=250)
    ap.add_argument('--fijos', nargs='*', default=[], help='parámetros que no se tocan')
    ap.add_argument('--valor', nargs='*', default=[], metavar='NOMBRE=VALOR', help='cambia el valor inicial')
    args = ap.parse_args()

    sys.path.insert(0, str(args.caso.resolve().parent))
    spec = importlib.util.spec_from_file_location('caso', args.caso)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for item in args.valor:
        name, value = item.split('=')
        module.PARAMS[name] = float(value)
    names = [n for n in module.PARAMS if n not in args.fijos]
    x0 = np.array([module.PARAMS[n] for n in names], dtype=float)
    scale = np.where(x0 != 0, np.abs(x0), 1.0)

    cells = load_all()
    visible = cells.hide_sw(CONTROL_WELLS)
    runs, t0 = 0, time.monotonic()

    with tempfile.TemporaryDirectory() as tmp:
        def objective(u: np.ndarray) -> float:
            nonlocal runs
            runs += 1
            p = dict(module.PARAMS) | dict(zip(names, u * scale))
            try:
                case = module.build(visible, p).resolved(len(cells))
                sw_sim, _ = initialize(case, cells, Path(tmp))
            except (ValueError, FlowError):
                return 1.0   # out of range: worse than any real case
            return puntaje.score(cells, sw_sim, case.n_parameters)['rmse_ajuste']

        start = objective(x0 / scale)
        best = minimize(objective, x0 / scale, method='Nelder-Mead',
                        options={'maxfev': args.max_corridas, 'xatol': 1e-3, 'fatol': 1e-5})

    final = dict(module.PARAMS) | dict(zip(names, best.x * scale))
    print(f'corridas: {runs}   segundos: {time.monotonic() - t0:.0f}')
    print(f'rmse inicial: {start:.4f}   rmse final: {best.fun:.4f}')
    print('PARAMS = {' + ', '.join(f"'{n}': {v:.4g}" for n, v in final.items()) + '}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
