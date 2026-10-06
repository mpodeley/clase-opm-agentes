"""Rebuild the two scans of block 8: the tilt of the contact and the perched water level under F-4.

    uv run docente/barridos.py

Tilt: each tilt was fitted on its own with docente/optimizar.py; the fitted sets are kept in
docente/plan-b/barrido_inclinacion_params.json and are only re-evaluated here.
Perched water: case P with its local level moved, everything else as fitted.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'docente' / 'soluciones'))

import evaluar  # noqa: E402
from sw import pozo, puntaje  # noqa: E402

OUT = ROOT / 'docente' / 'plan-b'
COLUMNS = ['rmse_ajuste', 'rmse_F-4', 'rmse_19-A', 'rmse_control_inicial', 'sesgo_control_inicial',
           'rmse_control_barrido', 'sesgo_control_barrido']
LOCAL_LEVELS = (2990, 3000, 3010, 3016, 3020, 3025, 3030, 3033, 3036, 3040, 3050, 3070, 3100)


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'docente' / 'soluciones' / f'{name}.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    cells = pozo.load_all()
    visible = cells.hide_sw(pozo.CONTROL_WELLS)
    tilted, perched = module('caso_t'), module('caso_p')
    tilt_sets = json.loads((OUT / 'barrido_inclinacion_params.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        def row(mod, params) -> list[float]:
            case = mod.build(visible, params).resolved(len(cells))
            sw, _ = evaluar.initialize(case, cells, Path(tmp))
            result = puntaje.score(cells, sw, case.n_parameters)
            return [result[c] for c in COLUMNS]

        lines = ['inclinacion_m_km\tfwl_19a_m\t' + '\t'.join(COLUMNS)]
        for p in tilt_sets:
            lines.append(f"{p['tilt_m_per_km']:g}\t{p['fwl_at_19a']:.0f}\t" + '\t'.join(f'{v:.4f}' for v in row(tilted, p)))
        (OUT / 'barrido_inclinacion.tsv').write_text('\n'.join(lines) + '\n')

        lines = ['fwl_f4_m\t' + '\t'.join(COLUMNS)]
        for level in LOCAL_LEVELS:
            lines.append(f'{level}\t' + '\t'.join(f'{v:.4f}' for v in row(perched, dict(perched.PARAMS, fwl_f4=float(level)))))
        (OUT / 'barrido_agua_colgada.tsv').write_text('\n'.join(lines) + '\n')
    print((OUT / 'barrido_inclinacion.tsv').read_text())
    print((OUT / 'barrido_agua_colgada.tsv').read_text())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
