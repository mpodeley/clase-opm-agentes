"""P: one J function, the regional free water level, and a perched water level under 15/9-F-4.

The base of the Hugin dips towards a fault where F-4 crosses it. If the fault seals, the low
corner of that block holds water that the oil could not displace: a local contact above the
regional one. In the deck that is a second equilibration region with its own level.
"""
import numpy as np

from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.021, 'j_entry': 0.274, 'lam': 0.275, 'fwl': 3146.0, 'fwl_f4': 3033.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    # The ranges the loop is held to (program.md), for the regional level.
    if not (3100.0 <= p['fwl'] <= 3220.0 and 0.02 <= p['swirr'] <= 0.60 and 2950.0 <= p['fwl_f4'] <= p['fwl']):
        raise ValueError('fuera del rango físico')
    return Case(
        description='P: una función J, contacto regional y agua colgada en F-4',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=[p['fwl'], p['fwl_f4']],
        eqlnum=np.where(cells.well == 'F-4', 2, 1),
        jfunc=JFunction(),
        n_parameters=len(p),
    )
