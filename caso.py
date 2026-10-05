"""The case under test: the only file the agent edits during the exercise.

`build(cells)` receives one entry per cell (see sw/pozo.py, class Cells) and returns the
way water saturation is initialized (see sw/modelo.py, class Case). Depths are metres below
sea level, positive down. `cells.sw` holds the log of F-12 and NaN for F-11 B, which is held
out to check the case afterwards.
"""
from sw.modelo import Case, brooks_corey
from sw.pozo import Cells


def build(cells: Cells) -> Case:
    # Base case: one capillary pressure curve for all rock and one free water level.
    return Case(
        description='A: curva única y un contacto',
        curves=[brooks_corey(swirr=0.10, pe=0.10, lam=1.0)],
        fwl=[2920.0],
        n_parameters=4,
    )
