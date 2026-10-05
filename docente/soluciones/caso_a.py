"""A: one capillary pressure curve for all rock and one free water level."""
from sw.modelo import Case, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.153, 'pe': 0.282, 'lam': 2.77, 'fwl': 2921.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='A: curva única y un contacto',
        curves=[brooks_corey(p['swirr'], p['pe'], p['lam'])],
        fwl=[p['fwl']],
        n_parameters=len(p),
    )
