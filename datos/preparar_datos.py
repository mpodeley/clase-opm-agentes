"""Fetch the Volve files the class needs into datos/volve/, pinned by sha256.

The files are public mirrors of Equinor's Volve data set (Equinor Open Data Licence).
Every URL is pinned to a commit and every file to its sha256, so a mirror that changes
stops the script instead of silently changing the exercise.

    uv run datos/preparar_datos.py            # download what is missing, verify everything
    uv run datos/preparar_datos.py --desde D  # copy from a local folder with the same layout
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent / 'volve'

AWGEO = 'https://raw.githubusercontent.com/awgeo/Volve_field_data/7cdecf1f1d24811d21bb2e2f379ff048404f4ce7'
PICKS = 'https://raw.githubusercontent.com/andymcdgeo/spwla_volve/c293edf37c1b567b8dc9c81ea88f2cf288eab423'
HUGIN = 'https://raw.githubusercontent.com/maribickpostanes/Interactive-Horizon-Surfaces-Plot/af617d2a25a90c02d45485127e82274ac9bad051'
PETRO = ('https://raw.githubusercontent.com/Joell2001/Petrofisica/e2d64f279d6fda8d34d1fc37f02a8d0803c3b512'
         '/Data/VOLVE-PETROPHYSICAL_INTERPRETATION')

# (path inside datos/volve/, pinned URL, sha256)
FILES = [
    ('perfiles/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     f'{PETRO}/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     '545ff15bc7fca12ff9660c07981be84c74e4c908206165718947457e9f1fc8bf'),
    ('perfiles/15_9-F-11 B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     f'{PETRO}/15_9-F-11%20B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     'e3fd166e295d4350d9a51bd338cb02a0ca3e72da9a5cb831641c999b6b015cec'),
    ('trayectorias/F-12_ACTUAL',
     f'{AWGEO}/input_data/wellpaths/F-12_ACTUAL',
     '34a1a6f6e1d73060e30af00114401392826e3870274e9d1e7314eba724c64477'),
    ('trayectorias/F-11 B_ACTUAL',
     f'{AWGEO}/input_data/wellpaths/F-11%20B_ACTUAL',
     '85e1d1f6b2f2dfd00d8a0d6aac2cc7c740e2f6958de830b8ad0dbde5a84a7411'),
    ('topes/Well_picks_Volve_v1.dat',
     f'{PICKS}/Well_picks_Volve_v1.dat',
     '1c132bba09555915b62e23dc4475f790a304856d369d9d26cc76466cf7b77d3a'),
    ('produccion/Volve production data.xlsx',
     f'{AWGEO}/input_data/Volve%20production%20data.xlsx',
     '514d4e38763e09be7fbad12313429909b9799b1a6ec999bf5f36e0df1b6c9cae'),
    ('mapas/Hugin_Fm_Top.csv',
     f'{HUGIN}/Hugin_Fm_Top.csv',
     '6bb2f7902f80beb9fd28ce177dc3a2aa3916d3dd4f4b33da9a72ee42f23bbd0b'),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': 'clase-opm-agentes/1.0'})
    part = dest.with_name(dest.name + '.part')
    with urllib.request.urlopen(req, timeout=120) as r, open(part, 'wb') as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    part.replace(dest)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--desde', type=Path, help='local folder with the same layout, used before the network')
    args = ap.parse_args()

    for rel, url, expected in FILES:
        dest = DEST / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            local = args.desde / rel if args.desde else None
            if local and local.exists():
                print(f'  copiando {rel}')
                shutil.copyfile(local, dest)
            else:
                print(f'  bajando  {rel}')
                download(url, dest)
        got = sha256(dest)
        if got != expected:
            print(f'sha256 distinto en {rel}: {got[:12]} (esperado {expected[:12]}). '
                  'El espejo cambió: revisar antes de usar.', file=sys.stderr)
            return 1
        print(f'  ok       {rel}  ({dest.stat().st_size / 1024:,.0f} KB)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
