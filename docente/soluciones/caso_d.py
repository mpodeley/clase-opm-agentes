"""D: one curve shape, connate water per cell from rock quality (end-point scaling)."""
import numpy as np

from sw.modelo import Case, brooks_corey
from sw.pozo import Cells

PARAMS = {'swl_at_1': 0.220, 'swl_slope': -0.097, 'pe': 0.061, 'lam': 1.26, 'fwl': 2913.0}


def connate_water(cells: Cells, p: dict) -> np.ndarray:
    # Linear in log10 of sqrt(k/phi): tighter rock holds more water.
    quality = np.log10(np.sqrt(cells.k / cells.phi))
    return np.clip(p['swl_at_1'] + p['swl_slope'] * quality, 0.02, 0.95)


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='D: extremos escalados por celda (SWL según calidad de roca)',
        curves=[brooks_corey(0.0, p['pe'], p['lam'])],
        swl=connate_water(cells, p),
        fwl=[p['fwl']],
        n_parameters=len(p),
    )
