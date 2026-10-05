"""Integration: what Flow initializes equals the saturation-height formula it is given."""
import os
import shutil

import numpy as np
import pytest

from evaluar import initialize
from sw import pozo
from sw.modelo import GRAVITY_BAR_PER_M, JFUNC_METRIC_CONSTANT, Case, JFunction, brooks_corey

pytestmark = pytest.mark.skipif(
    not (os.environ.get('FLOW') or shutil.which(os.environ.get('CONTENEDOR', 'podman'))),
    reason='no hay flow ni contenedor')

SWIRR, PE, LAM, FWL = 0.10, 0.10, 1.0, 2920.0


@pytest.fixture(scope='module')
def cells():
    return pozo.load_cells('F-12')


def saturation(pc: np.ndarray) -> np.ndarray:
    return np.where(pc <= PE, 1.0, SWIRR + (1 - SWIRR) * (np.maximum(pc, PE) / PE) ** (-LAM))


def test_single_curve_matches_the_height_function(cells, tmp_path):
    case = Case('prueba', [brooks_corey(SWIRR, PE, LAM, n=60)], [FWL], 4).resolved(len(cells))
    sw, _ = initialize(case, cells, tmp_path)
    expected = saturation(GRAVITY_BAR_PER_M * (FWL - cells.tvdss))
    assert np.max(np.abs(sw - expected)) < 0.02


def test_j_function_scales_with_rock_quality(cells, tmp_path):
    j = JFunction()
    case = Case('prueba', [brooks_corey(SWIRR, PE, LAM, n=60)], [FWL], 4, jfunc=j).resolved(len(cells))
    sw, _ = initialize(case, cells, tmp_path)
    factor = j.surface_tension * JFUNC_METRIC_CONSTANT * np.sqrt(cells.phi / cells.k)
    expected = saturation(GRAVITY_BAR_PER_M * (FWL - cells.tvdss) / factor)
    assert np.max(np.abs(sw - expected)) < 0.02


def test_swatinit_is_honoured_above_the_contact(cells, tmp_path):
    target = np.clip(cells.sw, 0.06, 1.0)
    case = Case('prueba', [brooks_corey(0.05, PE, LAM)], [3200.0], 4, swatinit=target).resolved(len(cells))
    sw, _ = initialize(case, cells, tmp_path)
    assert np.sqrt(np.mean((sw - target) ** 2)) < 0.02
