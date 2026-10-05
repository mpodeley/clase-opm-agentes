"""F0: the J function of case B with one flat contact, fitted on both wells at once."""
from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.045, 'j_entry': 0.029, 'lam': 0.290, 'fwl': 2986.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='F0: función J y un contacto plano para los dos pozos',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=[p['fwl']],
        jfunc=JFunction(),
        n_parameters=len(p),
    )
