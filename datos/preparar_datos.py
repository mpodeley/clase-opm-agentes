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

DECK = 'https://raw.githubusercontent.com/tpp-grupo-166/opm-datasets/76fbc78e60e641e0dbd3e587e07815dac4f4e679/models/volve'
WHITSON = 'https://raw.githubusercontent.com/WhitsonAS/Volve-Fluid-Model-Development/5e7298ed2cd86e02ef329ec6d5fd312b647e86f9'
JSONLOG = ('https://raw.githubusercontent.com/geosoft-as/jsonwelllogformat/35f523d84428bfd17588a7c3d0b9543cd8bd6c80'
           '/data/Volve/Well_logs')

# (path inside datos/volve/, pinned URL, sha256)
FILES = [
    # Interpreted logs: five wells logged before first oil, and the two controls (July 2008 and 2013).
    ('perfiles/15_9-19 SR/15_9-19_SR_CPI.las', f'{PETRO}/15_9-19%20SR/CPI/15_9-19_SR_CPI.las',
     'e4bd02b48733e465994809823187e7282119c784c396e29e130fed94eebb1ed8'),
    ('perfiles/15_9-19 A/15_9-19_A_CPI.las', f'{PETRO}/15_9-19%20A/CPI/15_9-19_A_CPI.las',
     '2b0bae3caa0c10f2f6fb3323cde198edcaf0e0ff3adb0c00308cf139cae9035b'),
    ('perfiles/15_9-19 BT2/15_9-19_BT2_CPI.las', f'{PETRO}/15_9-19%20BT2/CPI/15_9-19_BT2_CPI.las',
     'a74392b27450944ea973b16a800958a60e66b579496d218eba2f58bc54b424f9'),
    ('perfiles/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS', f'{PETRO}/15_9-F-12/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     '545ff15bc7fca12ff9660c07981be84c74e4c908206165718947457e9f1fc8bf'),
    ('perfiles/15_9-F-4/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS', f'{PETRO}/15_9-F-4/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS',
     '1cde69df90b9dcb5dff5807941c8b816d1db337140b3f654d14d5b8a975dbba7'),
    ('perfiles/15_9-F-5/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS', f'{PETRO}/15_9-F-5/WLC_PETRO_COMPUTED_OUTPUT_1.DLIS',
     '68e36fe12ebbc7046552194f9ce1f0f6cbffa5dd751610534127d06de4e506b7'),
    ('perfiles/15_9-F-11 B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS', f'{PETRO}/15_9-F-11%20B/WLC_PETRO_COMPUTED_OUTPUT_1.LAS',
     'e3fd166e295d4350d9a51bd338cb02a0ca3e72da9a5cb831641c999b6b015cec'),
    # The operator's 2009 revision of permeability.
    ('perfiles/15_9-F-12/KLOGH_NEW.las', f'{PETRO}/15_9-F-12/geomod09/NO_15_9-F-12_KLOGH_NEW.las',
     'aedc85027c7609212b8d18c4bb7d39fa1bf6582569053e8c365fe07d8c0dbba6'),
    ('perfiles/15_9-F-4/KLOGH_NEW.las', f'{PETRO}/15_9-F-4/geomod09/NO_15_9-F-4_KLOGH_NEW.las',
     '157e25fb42b1dfe74841e703081b7ecd4376501120814529127cfb65b2196641'),
    ('perfiles/15_9-F-5/KLOGH_NEW.las', f'{PETRO}/15_9-F-5/geomod09/NO_15_9-F-5_KLOGH_NEW.las',
     'e64691a9a2811695195aabae13d9c2744efc2be4da4b3a7fb15c518f3b117d10'),
    ('perfiles/15_9-19 BT2/KLOGH_NEW.las', f'{PETRO}/15_9-19%20BT2/geomod09/NO_15_9-19_BT2_KLOGH_NEW.las',
     '0bda4b605f7485d226fa3719e42e675cf538518c490034d860e8673a0918c9a9'),
    # Input logs for the quick look.
    ('perfiles/15_9-F-12/WLC_PETRO_COMPUTED_INPUT_1.LAS', f'{PETRO}/15_9-F-12/WLC_PETRO_COMPUTED_INPUT_1.LAS',
     '8d1a22ebed03f160d49fdfba72264868686e5c97c862faccc82cb6068dc52e30'),
    ('perfiles/15_9-F-4/WLC_PETRO_COMPUTED_INPUT_1.DLIS', f'{PETRO}/15_9-F-4/WLC_PETRO_COMPUTED_INPUT_1.DLIS',
     'ea47aaec916a05a7c49436de9c1a09a6181602aa4daf8a4e225d5e8e050b1503'),
    # Well paths, formation picks, surfaces, production.
    ('trayectorias/F-12_ACTUAL', f'{AWGEO}/input_data/wellpaths/F-12_ACTUAL',
     '34a1a6f6e1d73060e30af00114401392826e3870274e9d1e7314eba724c64477'),
    ('trayectorias/F-4_ACTUAL', f'{AWGEO}/input_data/wellpaths/F-4_ACTUAL',
     'e837fedc1bd7bc70588d7742ca598113bf019c9ddc2a79c85c5638d50fbb3c49'),
    ('trayectorias/F-5_ACTUAL', f'{AWGEO}/input_data/wellpaths/F-5_ACTUAL',
     '8f2a17efc256bf265aa808449956f95f8cabf6bc7366392194c2d0ccc199109c'),
    ('trayectorias/F-11 B_ACTUAL', f'{AWGEO}/input_data/wellpaths/F-11%20B_ACTUAL',
     '85e1d1f6b2f2dfd00d8a0d6aac2cc7c740e2f6958de830b8ad0dbde5a84a7411'),
    ('topes/Well_picks_Volve_v1.dat', f'{PICKS}/Well_picks_Volve_v1.dat',
     '1c132bba09555915b62e23dc4475f790a304856d369d9d26cc76466cf7b77d3a'),
    ('mapas/Hugin_Fm_Top.csv', f'{HUGIN}/Hugin_Fm_Top.csv',
     '6bb2f7902f80beb9fd28ce177dc3a2aa3916d3dd4f4b33da9a72ee42f23bbd0b'),
    ('mapas/Hugin_Fm_Base.csv', f'{HUGIN}/Hugin_Fm_Base.csv',
     '49f01696f493f0b07881729be318d5277eb43219387e628b41ea4c40d017d7ec'),
    ('mapas/BCU.csv', f'{HUGIN}/BCU.csv',
     '0051c5f2f8daafd349a7f5497d5947324b95b2bc85c7ca3ca0439fe8b52b181d'),
    ('produccion/Volve production data.xlsx', f'{AWGEO}/input_data/Volve%20production%20data.xlsx',
     '514d4e38763e09be7fbad12313429909b9799b1a6ec999bf5f36e0df1b6c9cae'),
    # Reference material: the operator's petrophysical report, the lab PVT report of the F-4 oil,
    # the field deck as adapted to OPM (read only, never run) and the 1998 pressure survey.
    ('referencia/statoil_3781-06_petrofisica_2006.pdf',
     f'{PETRO}/2005_Sleipner%20_%C3%98st_Hugin_Petrophysical_evaluation.pdf',
     '338c78d4872eac479aca213a6292bc7127a0ce3b7dbc3b8e959dd4eb91f0f2a0'),
    ('referencia/reslab_2008_pvt_F-4.pdf', f'{WHITSON}/PVT-Data/2008-Reslab-15-9-F4%20(Volve%20-%20MDT).pdf',
     'f493b6ca4e56a6afc31089871a5325b671d5763066f3401e0f1862df016bc89f'),
    ('referencia/VOLVE_2016.DATA', f'{DECK}/VOLVE_2016.DATA',
     '912eb03b5c8a3b86f618a77506cf0408043bae822cca68222144940b67fab477'),
    ('referencia/pvt_volve_2016.E100', f'{DECK}/pvt_input_new_combined_PVDG_020610_perch_water_2914m.E100',
     '1be6f7287b6ce1c22c3143fa62546483d5e9b5e850c6e46e4529f918bbd8c261'),
    ('presiones/L916RFT_19BT2.json', f'{JSONLOG}/03.PRESSURE/15_9-19%20BT2/L916RFT.json',
     '5788ceb14aaffd6267922213399b1055484d7c48567c8c7dbab5927817df5c27'),
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
