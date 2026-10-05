"""C: three rock types by sqrt(k/phi), one capillary pressure curve each."""
import numpy as np

from sw.modelo import Case, brooks_corey
from sw.pozo import Cells

# Class limits in sqrt(mD): fixed, taken from the terciles of F-12.
LIMITS = (0.9, 6.0)

PARAMS = {'swirr1': 0.087, 'pe1': 0.328, 'lam1': 0.929,
          'swirr2': 0.194, 'pe2': 0.138, 'lam2': 1.09,
          'swirr3': 0.022, 'pe3': 0.114, 'lam3': 0.836,
          'fwl': 2926.0}


def rock_type(cells: Cells) -> np.ndarray:
    return 1 + np.digitize(np.sqrt(cells.k / cells.phi), LIMITS)


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='C: tres tipos de roca por √(k/φ) y un contacto',
        curves=[brooks_corey(p[f'swirr{i}'], p[f'pe{i}'], p[f'lam{i}']) for i in (1, 2, 3)],
        satnum=rock_type(cells),
        fwl=[p['fwl']],
        n_parameters=len(p) + len(LIMITS),
    )
