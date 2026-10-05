"""J2: the operator's form. A normalized J function plus irreducible water linear in log k."""
import numpy as np

from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr_at_1md': 0.352, 'swirr_slope': -0.0610, 'j_entry': 3.44, 'lam': 1.67, 'fwl': 3151.0}


def irreducible(cells: Cells, p: dict) -> np.ndarray:
    # Swirr = c2 - c1 * log10(k): tighter rock holds more water (Statoil 3781-06, equation 21).
    return np.clip(p['swirr_at_1md'] + p['swirr_slope'] * np.log10(cells.k), 0.02, 0.90)


def build(cells: Cells, p: dict = PARAMS) -> Case:
    # The ranges the loop is held to (program.md).
    if not (3100.0 <= p['fwl'] <= 3220.0 and p['swirr_slope'] <= 0.0):
        raise ValueError('fuera del rango físico: FWL de 3,100 a 3,220 m, Swirr decreciente con k')
    return Case(
        description='J2: función J normalizada y Swirr según permeabilidad',
        curves=[brooks_corey(0.0, p['j_entry'], p['lam'])],   # Swn from 0 to 1, rescaled by SWL
        swl=irreducible(cells, p),
        fwl=[p['fwl']],
        jfunc=JFunction(),
        n_parameters=len(p),
    )
