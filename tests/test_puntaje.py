import numpy as np
import pytest

from sw import pozo, puntaje


@pytest.fixture(scope='module')
def cells():
    return pozo.load_all()


def test_the_log_scores_zero_against_itself(cells):
    r = puntaje.score(cells, cells.sw.copy(), 0)
    for key in ('rmse_ajuste', 'rmse_validacion', 'rmse_ajuste_hugin', 'sesgo_ajuste', 'error_hcpv_ajuste'):
        assert r[key] == pytest.approx(0.0, abs=1e-12)


def test_all_water_loses_all_the_hydrocarbon(cells):
    r = puntaje.score(cells, np.ones(len(cells)), 0)
    assert r['error_hcpv_ajuste'] == pytest.approx(-1.0)
    assert r['sesgo_ajuste'] > 0


def test_block_is_greppable(cells):
    text = puntaje.block('x', puntaje.score(cells, cells.sw, 3), 1.0)
    lines = text.splitlines()
    assert lines[0] == '---'
    assert any(line.startswith('rmse_ajuste: 0.0000') for line in lines)
    assert 'n_parametros: 3' in lines
