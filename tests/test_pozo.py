import numpy as np
import pytest

from sw import pozo


def test_trajectory_reproduces_the_picked_depths_of_f12():
    traj = pozo.load_trajectory(pozo.DATA / pozo.WELLS['F-12'].trajectory)
    tvdss = np.interp([3126.00, 3280.34], traj[:, 0], traj[:, 1]) - pozo.KB
    assert tvdss == pytest.approx([2818.39, 2909.63], abs=0.5)


def test_cells_start_at_the_top_of_the_hugin():
    cells = pozo.load_cells('F-12')
    assert cells.md[0] == pytest.approx(3126.0 + pozo.CELL_LENGTH / 2)
    assert cells.zone[0] == 'Hugin'
    assert set(cells.zone) == {'Hugin', 'Sleipner', 'Skagerrak'}


def test_cells_are_physical():
    cells = pozo.load_all()
    assert np.all((cells.sw >= 0) & (cells.sw <= 1))
    assert np.all(cells.phi >= pozo.MIN_PORO) and np.all(cells.k >= pozo.MIN_PERM)
    assert np.all(cells.dz > 0)
    assert np.all(np.diff(cells.md[cells.of('F-12')]) > 0)


def test_upscaling_keeps_the_water_volume_of_the_log():
    log = pozo.load_log('F-12')
    cells = pozo.load_cells('F-12')
    m = (log['md'] >= cells.md[0] - 0.5) & (log['md'] < cells.md[-1] + 0.5) & np.isfinite(log['phi'])
    bvw_log = np.mean(log['phi'][m] * log['sw'][m])
    bvw_cells = np.mean(cells.phi * cells.sw)
    assert bvw_cells == pytest.approx(bvw_log, rel=0.02)


def test_hide_sw_only_blanks_the_named_well():
    cells = pozo.load_all().hide_sw(['F-11 B'])
    assert np.all(np.isnan(cells.sw[cells.of('F-11 B')]))
    assert np.all(np.isfinite(cells.sw[cells.of('F-12')]))
