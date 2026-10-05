"""E: SWATINIT. The log is imposed cell by cell and Flow rescales capillary pressure to hold it."""
from sw.modelo import Case, brooks_corey
from sw.pozo import Cells

# The contact is set below the logged interval: Flow ignores SWATINIT under the free water level.
PARAMS = {'swirr': 0.02, 'pe': 0.10, 'lam': 1.0, 'fwl': 3200.0}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    known = int((cells.sw == cells.sw).sum())   # cells with a log value: each one is a parameter
    return Case(
        description='E: SWATINIT con el perfil celda a celda',
        curves=[brooks_corey(p['swirr'], p['pe'], p['lam'])],
        fwl=[p['fwl']],
        swatinit=cells.sw,        # NaN where there is no log: equilibration decides there
        n_parameters=len(p) + known,
    )
