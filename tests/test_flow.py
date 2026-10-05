"""Integration: what Flow initializes equals the saturation-height formula it is given."""
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

import evaluar
from sw import pozo
from sw.modelo import GRAVITY_BAR_PER_M, JFUNC_METRIC_CONSTANT, SIGMA_COS_THETA, Case, JFunction, brooks_corey

pytestmark = pytest.mark.skipif(
    not (os.environ.get('FLOW') or shutil.which(os.environ.get('CONTENEDOR', 'podman'))),
    reason='no hay flow ni contenedor')

J_ENTRY, LAM, FWL = 2.0, 1.0, 3120.0


@pytest.fixture(scope='module')
def cells():
    return pozo.load_all()


def leverett_j(cells) -> np.ndarray:
    pc = GRAVITY_BAR_PER_M * np.maximum(FWL - cells.tvdss, 0.0)
    return pc * np.sqrt(cells.k / cells.phi) / (SIGMA_COS_THETA * JFUNC_METRIC_CONSTANT)


def normalized(j: np.ndarray) -> np.ndarray:
    return np.where(j <= J_ENTRY, 1.0, (np.maximum(j, J_ENTRY) / J_ENTRY) ** (-LAM))


def test_j_function_matches_the_closed_form(cells, tmp_path):
    swirr = 0.10
    case = Case('prueba', [brooks_corey(swirr, J_ENTRY, LAM, n=80)], [FWL], 4, jfunc=JFunction())
    sw, _ = evaluar.initialize(case.resolved(len(cells)), cells, tmp_path)
    expected = swirr + (1 - swirr) * normalized(leverett_j(cells))
    assert np.max(np.abs(sw - expected)) < 0.02


def test_connate_water_per_cell_gives_the_operator_form(cells, tmp_path):
    """Sw = Swn * (1 - Swirr) + Swirr, with Swirr set cell by cell through SWL."""
    swirr = np.clip(0.45 - 0.105 * np.log10(cells.k), 0.02, 0.90)
    case = Case('prueba', [brooks_corey(0.0, J_ENTRY, LAM, n=80)], [FWL], 5, jfunc=JFunction(), swl=swirr)
    sw, _ = evaluar.initialize(case.resolved(len(cells)), cells, tmp_path)
    expected = swirr + (1 - swirr) * normalized(leverett_j(cells))
    assert np.max(np.abs(sw - expected)) < 0.02


def test_a_case_never_sees_the_control_well(cells, tmp_path):
    probe = tmp_path / 'caso_espia.py'
    probe.write_text(
        'import numpy as np\n'
        'from sw.modelo import Case, JFunction, brooks_corey\n'
        'def build(cells):\n'
        '    assert np.all(np.isnan(cells.sw[cells.well == "F-11 B"]))\n'
        '    assert np.all(np.isfinite(cells.sw[cells.well != "F-11 B"]))\n'
        '    return Case("espia", [brooks_corey(0.1, 2.0, 1.0)], [3120.0], 4, jfunc=JFunction())\n')
    evaluar.load_case(Path(probe), cells.hide_sw(pozo.CONTROL_WELLS))
