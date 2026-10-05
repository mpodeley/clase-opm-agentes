import numpy as np
import pytest

from sw import pozo

# Hugin top and base in m TVDSS, from the picks file.
HUGIN = {'19 SR': (2861.41, 2879.66), '19 A': (3012.99, 3101.40), '19 BT2': (3148.92, 3274.68),
         'F-12': (2818.39, 2909.63), 'F-4': (2931.04, 3033.32)}


@pytest.mark.parametrize('well', ['F-12', 'F-4'])
def test_survey_reproduces_the_picked_depths(well):
    top, base = pozo.hugin_intervals(pozo.WELLS[well].picks_name)[0]
    tvdss, _, _ = pozo.position(well, np.array([top, base]))
    assert tvdss == pytest.approx(HUGIN[well], abs=0.5)


@pytest.mark.parametrize('well', list(HUGIN))
def test_cells_stay_inside_the_hugin(well):
    cells = pozo.load_cells(well)
    top, base = HUGIN[well]
    assert cells.tvdss.min() >= top and cells.tvdss.max() <= base
    assert cells.net.sum() >= 20


def test_fit_and_control_wells():
    assert pozo.FIT_WELLS == ['19 SR', '19 A', '19 BT2', 'F-12', 'F-4']
    assert pozo.CONTROL_WELLS == ['F-11 B']
    assert len(pozo.hugin_intervals(pozo.WELLS['F-11 B'].picks_name)) > 1   # faulted: several stretches


def test_cells_are_physical():
    cells = pozo.load_all()
    assert np.all((cells.sw >= 0) & (cells.sw <= 1))
    assert np.all(cells.phi >= pozo.MIN_PORO) and np.all(cells.k >= pozo.MIN_PERM)
    assert np.all(cells.dz > 0)


def test_revised_permeability_is_used_in_f12():
    cells = pozo.load_cells('F-12')
    assert np.exp(np.log(cells.k[cells.net]).mean()) > 100   # the 2007 file gives about 17 mD


def test_water_leg_well_reads_as_water():
    cells = pozo.load_cells('19 BT2')
    assert cells.sw[cells.net].mean() > 0.9


def test_upscaling_keeps_the_water_volume_of_the_log():
    log, cells = pozo.load_log('F-12'), pozo.load_cells('F-12')
    m = (log['md'] >= cells.md[0] - 0.5) & (log['md'] < cells.md[-1] + 0.5) & np.isfinite(log['phi'])
    assert np.mean(cells.phi * cells.sw) == pytest.approx(np.mean(log['phi'][m] * log['sw'][m]), rel=0.02)


def test_hide_sw_only_blanks_the_named_well():
    cells = pozo.load_all().hide_sw(pozo.CONTROL_WELLS)
    assert np.all(np.isnan(cells.sw[cells.of('F-11 B')]))
    assert np.all(np.isfinite(cells.sw[np.isin(cells.well, pozo.FIT_WELLS)]))
