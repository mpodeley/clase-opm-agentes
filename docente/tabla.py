"""Evaluate every reference case and write the comparison the class is built on.

    uv run docente/tabla.py

Writes docente/plan-b/<case>/ (deck, Flow output, figure) and docente/plan-b/tabla.md.
Cases F0, F1 and F2 are fitted on both wells, so they run with --ver-validacion.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docente' / 'plan-b'
CASES = [('a', False), ('b', False), ('c', False), ('d', False), ('e', False),
         ('f0', True), ('f1', True), ('f2', True)]
COLUMNS = ['rmse_ajuste', 'rmse_ajuste_hugin', 'rmse_ajuste_bajo_hugin', 'error_hcpv_ajuste',
           'rmse_validacion', 'error_hcpv_validacion', 'n_parametros']


def main() -> int:
    rows = []
    for name, both in CASES:
        cmd = [sys.executable, str(ROOT / 'evaluar.py'), '--caso', str(ROOT / 'docente' / 'soluciones' / f'caso_{name}.py'),
               '--salida', str(OUT / name)] + (['--ver-validacion'] if both else [])
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return 1
        values = dict(line.split(': ', 1) for line in proc.stdout.splitlines() if ': ' in line)
        rows.append((values['caso'], 'los dos' if both else 'F-12', values))
        print(f'{name:3} {values["rmse_ajuste"]}  {values["rmse_validacion"]}  {values["caso"]}')

    lines = ['| Caso | Ajustado con | ' + ' | '.join(COLUMNS) + ' |', '| --- | --- |' + ' ---: |' * len(COLUMNS)]
    for description, fitted, values in rows:
        cells = [f'{float(values[c]):+.1%}' if c.startswith('error_') else values[c] for c in COLUMNS]
        lines.append(f'| {description} | {fitted} | ' + ' | '.join(cells) + ' |')
    (OUT / 'tabla.md').write_text('\n'.join(lines) + '\n')
    print(f'escrito {OUT / "tabla.md"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
