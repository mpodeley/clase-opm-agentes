import numpy as np
import pytest

from sw import pozo, puntaje


@pytest.fixture(scope='module')
def cells():
    return pozo.load_all()


def test_the_log_scores_zero_against_itself(cells):
    r = puntaje.score(cells, cells.sw.copy(), 0)
    for key in ('rmse_ajuste', 'rmse_control_inicial', 'rmse_control_barrido', 'rmse_F-12', 'rmse_19-BT2', 'sesgo_ajuste', 'error_hcpv_ajuste'):
        assert r[key] == pytest.approx(0.0, abs=1e-12)


def test_only_net_cells_of_the_right_wells_count(cells):
    sim = cells.sw.copy()
    sim[~cells.net] = 0.0                      # wreck the non-net cells
    assert puntaje.score(cells, sim, 0)['rmse_ajuste'] == pytest.approx(0.0, abs=1e-12)
    sim = cells.sw.copy()
    sim[cells.of('F-11 B')] = 1.0              # wreck the swept control only
    r = puntaje.score(cells, sim, 0)
    assert r['rmse_ajuste'] == pytest.approx(0.0, abs=1e-12) and r['rmse_control_barrido'] > 0.5
    assert r['rmse_control_inicial'] == pytest.approx(0.0, abs=1e-12)


def test_all_water_loses_all_the_hydrocarbon(cells):
    r = puntaje.score(cells, np.ones(len(cells)), 0)
    assert r['error_hcpv_ajuste'] == pytest.approx(-1.0)


def test_block_is_greppable(cells):
    lines = puntaje.block('x', puntaje.score(cells, cells.sw, 3), [3120.0], 1.0).splitlines()
    assert lines[0] == '---'
    assert any(line.startswith('rmse_ajuste: 0.0000') for line in lines)
    assert 'n_parametros: 3' in lines and 'fwl: 3120.0' in lines
