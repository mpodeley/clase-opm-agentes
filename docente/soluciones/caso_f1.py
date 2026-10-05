"""F1: J function with one free water level per formation group (Hugin against what lies below)."""
import numpy as np

from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.042, 'j_entry': 0.076, 'lam': 0.257, 'fwl_hugin': 3156.0, 'fwl_below': 2937.0}

UPPER = ('Hugin', 'Heather', 'bajo Hugin')   # F-11 B re-enters the Hugin across faults


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='F1: función J, un contacto para Hugin y otro para Sleipner y Skagerrak',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=[p['fwl_hugin'], p['fwl_below']],
        eqlnum=np.where(np.isin(cells.zone, UPPER), 1, 2),
        jfunc=JFunction(),
        n_parameters=len(p),
    )
