"""The case under test: the only file the agent edits during the exercise.

`build(cells)` receives one entry per cell (see sw/pozo.py, class Cells) and returns the
way water saturation is initialized (see sw/modelo.py, class Case). Depths are metres below
sea level, positive down. `cells.sw` holds the log of the five wells logged before production
and NaN for the control well, 15/9-F-11 B.
"""
from sw.modelo import Case, JFunction, brooks_corey
from sw.pozo import Cells


def build(cells: Cells) -> Case:
    # Base case: one Leverett J function for all the Hugin and one free water level.
    return Case(
        description='J1: una función J y un contacto',
        curves=[brooks_corey(swirr=0.10, pe=2.0, lam=1.0)],
        fwl=[3120.0],
        jfunc=JFunction(),
        n_parameters=4,
    )
