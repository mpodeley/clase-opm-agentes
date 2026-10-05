import numpy as np
import pytest

from sw import pozo
from sw.modelo import FIT_FILES, MAX_PARAMETERS, Case, JFunction, brooks_corey, fragment, write_deck


@pytest.fixture(scope='module')
def cells():
    return pozo.load_all()


def simple(**kw) -> Case:
    base = dict(description='prueba', curves=[brooks_corey(0.1, 2.0, 1.0)], fwl=[3120.0], n_parameters=4,
                jfunc=JFunction())
    return Case(**(base | kw))


def test_brooks_corey_is_a_valid_drainage_table():
    c = brooks_corey(0.12, 0.2, 1.5)
    assert c.sw[-1] == 1.0 and c.pc[-1] == pytest.approx(0.2)
    assert np.all(np.diff(c.sw) > 0) and np.all(np.diff(c.pc) < 0)
    assert c.sw[0] > 0.12


@pytest.mark.parametrize('kw', [
    {},
    {'jfunc': None},
    {'curves': [brooks_corey(0.1, 2.0, 1.0), brooks_corey(0.3, 5.0, 0.8)], 'satnum': 'alternate'},
    {'fwl': [3120.0, 3030.0], 'eqlnum': 'alternate'},
    {'swl': 'constant'},
])
def test_deck_with_its_includes_parses_with_opm(cells, kw, tmp_path):
    opm_io = pytest.importorskip('opm.io')
    n = len(cells)
    fill = {'alternate': 1 + np.arange(n) % 2, 'constant': np.full(n, 0.3)}
    case = simple(**{k: fill[v] if isinstance(v, str) else v for k, v in kw.items()})
    deck = opm_io.Parser().parse(str(write_deck(case, cells, tmp_path)))
    assert deck['DIMENS'][0][0].get_int(0) == n
    assert 'EQUIL' in deck and 'SWOF' in deck
    assert ('JFUNC' in deck) == (case.jfunc is not None)


def test_a_change_of_case_only_touches_the_fit_files(cells, tmp_path):
    a = write_deck(simple(), cells, tmp_path / 'a').parent
    b = write_deck(simple(fwl=[3150.0], curves=[brooks_corey(0.05, 3.0, 0.8)]), cells, tmp_path / 'b').parent
    changed = {f.name for f in a.iterdir() if f.read_text() != (b / f.name).read_text()}
    assert changed == {'AJUSTE_PROPS.INC', 'AJUSTE_SOLUTION.INC'}
    assert changed <= set(FIT_FILES)


def test_fragment_shows_the_fit_and_stays_short(cells, tmp_path):
    n = len(cells)
    text = fragment(write_deck(simple(swl=np.full(n, 0.2)), cells, tmp_path).parent)
    assert 'JFUNC' in text and 'EQUIL' in text and ' 3120.000 ' in text
    assert f'SWL   -- {n} valores' in text
    assert len(text.splitlines()) < 40


@pytest.mark.parametrize('kw, message', [
    ({'satnum': np.full(5, 1)}, 'satnum'),
    ({'eqlnum': 'twos'}, 'eqlnum'),
    ({'swl': 'too_big'}, 'swl'),
    ({'n_parameters': MAX_PARAMETERS + 1}, 'máximo'),
])
def test_bad_cases_are_rejected_with_a_message(cells, kw, message):
    n = len(cells)
    fill = {'twos': np.full(n, 2), 'too_big': np.full(n, 1.5)}
    case = simple(**{k: fill[v] if isinstance(v, str) else v for k, v in kw.items()})
    with pytest.raises(ValueError, match=message):
        case.resolved(n)
