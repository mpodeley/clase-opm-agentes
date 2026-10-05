import json

import bitacora


def test_commit_message_carries_hypothesis_mechanism_and_prediction():
    parsed = bitacora.parse_message('La curva no tiene meseta\n\nmecanismo: la roca retiene poco\nPredicción: de 0.14 a 0.11\n')
    assert parsed == {'hipotesis': 'La curva no tiene meseta', 'mecanismo': 'la roca retiene poco',
                      'prediccion': 'de 0.14 a 0.11'}


def test_logbook_joins_runs_with_their_verdict(tmp_path):
    for n, (commit, fit) in enumerate([('aaa1111', 0.14), ('bbb2222', 0.11)], 1):
        folder = tmp_path / 'corridas' / f'exp-{n:02d}-{commit}'
        folder.mkdir(parents=True)
        (folder / 'registro.json').write_text(json.dumps(
            {'commit': commit, 'mensaje': f'hipótesis {n}\n\nprediccion: baja', 'rmse_ajuste': fit,
             'rmse_control': 0.2, 'n_parametros': 4}))
        (folder / 'fragmento.txt').write_text(f'EQUIL\n {3100 + n}.000 /\n')
    (tmp_path / 'results.tsv').write_text(
        'commit\trmse_ajuste\trmse_control\tn_parametros\tstatus\tlectura\n'
        'aaa1111\t0.14\t0.2\t4\tkeep\tbase\nbbb2222\t0.11\t0.2\t4\tdiscard\tno alcanzó\n')
    experiments = bitacora.load(tmp_path)
    assert [e['status'] for e in experiments] == ['keep', 'discard']
    assert experiments[1]['hipotesis'] == 'hipótesis 2' and experiments[1]['lectura'] == 'no alcanzó'
    assert '3102.000' in experiments[1]['diff'] and experiments[0]['diff'] == ''
    page = bitacora.page(experiments)
    assert 'hipótesis 2' in page and '<svg' in page
    assert '| 2 | hipótesis 2 | baja |' in bitacora.table_markdown(experiments)
