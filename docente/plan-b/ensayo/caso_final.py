"""The case under test: the only file the agent edits during the exercise.

`build(cells)` receives one entry per cell (see sw/pozo.py, class Cells) and returns the
way water saturation is initialized (see sw/modelo.py, class Case). Depths are metres below
sea level, positive down. `cells.sw` holds the log of the five wells logged before production
and NaN for the control well, 15/9-F-11 B.
"""
from sw.modelo import Case, JFunction, PcCurve, brooks_corey
from sw.pozo import Cells

B = 0.284              # Sw = J^-B: water saturation reaches 1 at J = 1
FWL = 3150.0           # m TVDSS, at the top of the water seen in 19 BT2


def lambda_curve(b: float, a: float = 1.0) -> PcCurve:
    """Sw = a * J^-b with no irreducible plateau: Brooks-Corey with swirr = 0 and pe = a^(1/b)."""
    return brooks_corey(swirr=0.0, pe=a ** (1.0 / b), lam=b)


def build(cells: Cells) -> Case:
    # One Leverett J function for all the Hugin, without a plateau, and one free water level.
    return Case(
        description='L3: Sw = J^-b sin meseta y un contacto',
        curves=[lambda_curve(B)],
        fwl=[FWL],
        jfunc=JFunction(),
        n_parameters=2,
    )
