"""The case under test: the only file the agent edits during the exercise.

`build(cells)` receives one entry per cell (see sw/pozo.py, class Cells) and returns the
way water saturation is initialized (see sw/modelo.py, class Case). Depths are metres below
sea level, positive down. `cells.sw` holds the log of F-12 and NaN for F-11 B, which is held
out to check the case afterwards.
"""
import numpy as np

from sw.modelo import Case, JFunction, PcCurve
from sw.pozo import Cells

SW_FLOOR = 0.02   # lower end of the tables: the lowest irreducible saturation the brief allows


def log_linear(a: float, b: float, n: int = 80) -> PcCurve:
    """Sw = a - b * ln(J), written as a table of J against Sw from SW_FLOOR to 1."""
    sw = np.linspace(SW_FLOOR, 1.0, n)
    return PcCurve(sw=sw, pc=np.exp((a - sw) / b))


def build(cells: Cells) -> Case:
    # Two curves that are straight lines in ln(J), split at the base of the Hugin (a pick, not
    # a fitted number) and sharing the slope, with one free water level. JFUNC is used with
    # exponents -1 for porosity and 0 for permeability, so J is proportional to Pc * phi:
    # Sw depends on height above the free water level times porosity, and KLOGH is not used.
    # It is not Leverett scaling. The exponents were fixed after a free fit landed next to them.
    hugin = cells.zone == 'Hugin'
    return Case(
        description='Sw lineal en ln(altura x porosidad), dos formaciones, un contacto',
        curves=[log_linear(a=-0.3854, b=0.3744),
                log_linear(a=-0.0334, b=0.3744)],
        satnum=np.where(hugin, 1, 2),
        fwl=[3191.6],
        jfunc=JFunction(alpha=-1.0, beta=0.0),
        n_parameters=4,
    )
