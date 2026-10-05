import numpy as np
import pytest

from sw import pozo
from sw.modelo import Case, JFunction, brooks_corey, deck_text


@pytest.fixture(scope='module')
def cells():
    return pozo.load_all()


def simple(**kw) -> Case:
    base = dict(description='prueba', curves=[brooks_corey(0.1, 0.1, 1.0)], fwl=[2920.0], n_parameters=4)
    return Case(**(base | kw))


def test_brooks_corey_is_a_valid_drainage_table():
    c = brooks_corey(0.12, 0.2, 1.5)
    assert c.sw[-1] == 1.0 and c.pc[-1] == pytest.approx(0.2)
    assert np.all(np.diff(c.sw) > 0) and np.all(np.diff(c.pc) < 0)
    assert c.sw[0] > 0.12


@pytest.mark.parametrize('kw', [
    {},
    {'jfunc': JFunction()},
    {'curves': [brooks_corey(0.1, 0.1, 1.0), brooks_corey(0.3, 0.5, 0.8)], 'satnum': 'alternate'},
    {'fwl': [2920.0, 3150.0], 'eqlnum': 'alternate'},
    {'swl': 'constant'},
    {'swatinit': 'constant', 'ppcwmax': 20.0},
])
def test_deck_parses_with_opm(cells, kw, tmp_path):
    opm_io = pytest.importorskip('opm.io')
    n = len(cells)
    fill = {'alternate': 1 + np.arange(n) % 2, 'constant': np.full(n, 0.3)}
    case = simple(**{k: fill[v] if isinstance(v, str) else v for k, v in kw.items()})
    path = tmp_path / 'SW.DATA'
    path.write_text(deck_text(case, cells))
    deck = opm_io.Parser().parse(str(path))
    assert deck['DIMENS'][0][0].get_int(0) == n


@pytest.mark.parametrize('kw, message', [
    ({'satnum': np.full(5, 1)}, 'satnum'),
    ({'eqlnum': 'twos'}, 'eqlnum'),
    ({'swl': 'too_big'}, 'swl'),
    ({'swatinit': 'half', 'jfunc': JFunction()}, 'swatinit'),
])
def test_bad_cases_are_rejected_with_a_message(cells, kw, message):
    n = len(cells)
    fill = {'twos': np.full(n, 2), 'too_big': np.full(n, 1.5), 'half': np.full(n, 0.5)}
    case = simple(**{k: fill[v] if isinstance(v, str) else v for k, v in kw.items()})
    with pytest.raises(ValueError, match=message):
        case.resolved(n)
