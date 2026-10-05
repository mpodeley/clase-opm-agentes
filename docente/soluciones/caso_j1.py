"""J1: one Leverett J function for the whole Hugin and one free water level."""
from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

PARAMS = {'swirr': 0.02, 'j_entry': 0.298, 'lam': 0.243, 'fwl': 3150.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    # The ranges the loop is held to (program.md).
    if not (3100.0 <= p['fwl'] <= 3220.0 and 0.02 <= p['swirr'] <= 0.60):
        raise ValueError('fuera del rango físico: FWL de 3,100 a 3,220 m, Swirr de 0.02 a 0.60')
    return Case(
        description='J1: una función J y un contacto',
        curves=[brooks_corey(p['swirr'], p['j_entry'], p['lam'])],
        fwl=[p['fwl']],
        jfunc=JFunction(),
        n_parameters=len(p),
    )
