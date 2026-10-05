"""OP: the operator's model as tabulated, with nothing fitted here.

Statoil doc. 3781-06 (2006), table 11, Volve Hugin: Swn = 2.222 * J^-1.111, sigma*cos(theta) = 2,
Swirr = 0.45 - 0.105 * log10(k), and a free water level of 3,120 m TVDSS (table 10).
The report is not consistent with itself: its figure 20.b labels 0.412 - 0.088 * log10(k) as
the Volve line, and figure 5.b shows a different J curve. This case follows the table.
"""
from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells

from caso_j2 import irreducible

A, B = 2.222, 1.111
PARAMS = {'swirr_at_1md': 0.45, 'swirr_slope': -0.105}


def build(cells: Cells, p: dict = PARAMS) -> Case:
    return Case(
        description='OP: el modelo del operador (2006), sin ajustar',
        curves=[brooks_corey(0.0, A ** (1.0 / B), B)],
        swl=irreducible(cells, p),
        fwl=[3120.0],
        jfunc=JFunction(),
        n_parameters=0,
    )
