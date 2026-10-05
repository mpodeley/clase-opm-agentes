"""T: the J2 form with a tilted free water level, as steps of equilibration regions.

The tilt is taken along the direction from 15/9-19 A to 15/9-F-4, the two fitted wells whose
logs reach closest to water, and is the only thing added to J2.
"""
import numpy as np

from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

from caso_j2 import irreducible

X0, Y0 = 436188.0, 6478714.0   # top of the Hugin in 15/9-19 A
AZIMUTH = 209.5                # degrees from north, towards the top of the Hugin in 15/9-F-4
STEPS = 30

PARAMS = {'swirr_at_1md': 0.255, 'swirr_slope': -0.0569, 'j_entry': 0.193, 'lam': 0.375,
          'fwl_at_19a': 3127.0, 'tilt_m_per_km': -90.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    if not 3100.0 <= p['fwl_at_19a'] <= 3220.0:
        raise ValueError('fuera del rango físico: FWL en 19 A de 3,100 a 3,220 m')
    az = np.radians(AZIMUTH)
    distance_km = ((cells.x - X0) * np.sin(az) + (cells.y - Y0) * np.cos(az)) / 1000.0
    edges = np.linspace(distance_km.min(), distance_km.max(), STEPS + 1)
    centres = 0.5 * (edges[:-1] + edges[1:])
    return Case(
        description='T: J2 con contacto inclinado de 19 A hacia F-4',
        curves=[brooks_corey(0.0, p['j_entry'], p['lam'])],
        swl=irreducible(cells, p),
        fwl=list(p['fwl_at_19a'] + p['tilt_m_per_km'] * centres),
        eqlnum=np.clip(np.digitize(distance_km, edges), 1, STEPS),
        jfunc=JFunction(),
        n_parameters=len(p),
    )
