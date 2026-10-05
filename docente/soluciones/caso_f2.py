"""F2: J function with a tilted free water level, as steps of equilibration regions."""
import numpy as np

from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

# Reference point (top of the Hugin in F-12) and the direction towards F-11 B.
X0, Y0 = 435029.3, 6478277.7
AZIMUTH = 85.0   # degrees from north
STEPS = 40

PARAMS = {'swirr': 0.058, 'j_entry': 0.070, 'lam': 0.285, 'fwl_at_f12': 2994.0, 'tilt_m_per_km': 104.8}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    az = np.radians(AZIMUTH)
    distance_km = ((cells.x - X0) * np.sin(az) + (cells.y - Y0) * np.cos(az)) / 1000.0
    edges = np.linspace(distance_km.min(), distance_km.max(), STEPS + 1)
    centres = 0.5 * (edges[:-1] + edges[1:])
    return Case(
        description='F2: función J y contacto inclinado hacia F-11 B',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=list(p['fwl_at_f12'] + p['tilt_m_per_km'] * centres),
        eqlnum=np.clip(np.digitize(distance_km, edges), 1, STEPS),
        jfunc=JFunction(),
        n_parameters=len(p),
    )
