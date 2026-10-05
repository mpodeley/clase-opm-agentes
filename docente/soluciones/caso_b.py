"""B: Leverett J function. One dimensionless curve, scaled per cell by sqrt(k/phi)."""
from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.089, 'j_entry': 0.0075, 'lam': 0.612, 'fwl': 2918.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='B: función J de Leverett y un contacto',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=[p['fwl']],
        jfunc=JFunction(),
        n_parameters=len(p),
    )
