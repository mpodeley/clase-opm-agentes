"""Evaluate every reference case and write the comparison the class is built on.

    uv run docente/tabla.py

Writes docente/plan-b/<case>/ (deck, Flow output, fragment, figure) and docente/plan-b/tabla.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docente' / 'plan-b'
CASES = ['base', 'j1', 'op', 'j2', 't', 'p']
COLUMNS = ['rmse_ajuste', 'rmse_19-SR', 'rmse_19-A', 'rmse_19-BT2', 'rmse_F-12', 'rmse_F-4',
           'rmse_control_inicial', 'sesgo_control_inicial', 'rmse_control_barrido', 'sesgo_control_barrido',
           'error_hcpv_ajuste', 'fwl', 'n_parametros']


def main() -> int:
    rows = []
    for name in CASES:
        case = ROOT / 'caso.py' if name == 'base' else ROOT / 'docente' / 'soluciones' / f'caso_{name}.py'
        cmd = [sys.executable, str(ROOT / 'evaluar.py'), '--caso', str(case), '--salida', str(OUT / name)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return 1
        values = dict(line.split(': ', 1) for line in proc.stdout.splitlines() if ': ' in line)
        if name == 'base':
            values['caso'] = 'Base: J1 sin ajustar'
        rows.append(values)
        print(f'{name:5} {values["rmse_ajuste"]}  {values["rmse_control_inicial"]}  {values["rmse_control_barrido"]}  {values["caso"]}')

    lines = ['| Caso | ' + ' | '.join(COLUMNS) + ' |', '| --- |' + ' ---: |' * len(COLUMNS)]
    for values in rows:
        cells = [f'{float(values[c]):+.1%}' if c.startswith('error_') else values[c] for c in COLUMNS]
        lines.append(f'| {values["caso"]} | ' + ' | '.join(cells) + ' |')
    (OUT / 'tabla.md').write_text('\n'.join(lines) + '\n')
    print(f'escrito {OUT / "tabla.md"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
