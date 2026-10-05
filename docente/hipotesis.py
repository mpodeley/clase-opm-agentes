"""Put the hypotheses of the rehearsed loop into the slides and the public page.

    uv run docente/hipotesis.py

Reads docente/plan-b/ensayo/ with the same code as bitacora.py and rewrites the text between
the HIPOTESIS markers in slides/clase.md and web/index.html, so that the three say the same.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import bitacora  # noqa: E402

PER_SLIDE = 4
VERDICT = {'keep': 'Queda', 'discard': 'Se descarta', 'crash': 'Falló'}
NOTES = ('Tabla del ensayo, tal como la escribió el agente: cada hipótesis es la\n'
         'primera línea de un commit anterior a la corrida.\nLeer dos o tres en voz alta: una que quedó, '
         'una que se descartó por\nel criterio de simplicidad y una que empeoró.')


def number(value) -> str:
    return f'{value:.3f}' if isinstance(value, float) else ''


def slides(experiments: list[dict]) -> str:
    """The deck shows the hypotheses and what came of them; the predictions are in the animation."""
    chunks = [experiments[i:i + PER_SLIDE] for i in range(0, len(experiments), PER_SLIDE)]
    out = []
    for i, chunk in enumerate(chunks):
        title = 'Las hipótesis que surgieron' + (f' ({i + 1} de {len(chunks)})' if len(chunks) > 1 else '')
        lines = ['<style scoped>table { font-size: 19px; line-height: 1.3; width: 100%; } td { padding: 8px 14px 8px 0; } '
                 'td:nth-child(2) { font-family: inherit; font-size: 19px; color: inherit; white-space: normal; } '
                 'h2 { margin-bottom: 8px; max-width: none; }</style>', '', f'## {title}', '',
                 '| N.º | Hipótesis | Ajuste | Control | Parámetros | Veredicto |',
                 '| ---: | --- | ---: | ---: | ---: | --- |']
        for e in chunk:
            lines.append(f"| {e['n']} | {e['hipotesis']} | {number(e.get('rmse_ajuste'))} | "
                         f"{number(e.get('rmse_control'))} | {e.get('n_parametros', '—')} | {VERDICT.get(e['status'], e['status'])} |")
        minutes = 6 // len(chunks)
        clock = 3 * 60 + (i + 1) * minutes
        note = (f'{minutes} min · acumulado {clock // 60}:{clock % 60:02d}\n'
                + (NOTES if i == 0 else 'Preguntar antes de mostrar el veredicto: ¿esta la conservarían?'))
        out.append('\n'.join(lines) + f'\n\n<!--\n{note}\n-->')
    return '\n\n---\n\n'.join(out)


def table_html(experiments: list[dict]) -> str:
    rows = ['<div class="scroll"><table>',
            '<tr><th class="n">N.º</th><th>Hipótesis</th><th>Predicción</th><th class="n">Ajuste</th>'
            '<th class="n">Control</th><th>Veredicto</th></tr>']
    for e in experiments:
        rows.append(f'<tr><td class="n">{e["n"]}</td><td>{html.escape(e["hipotesis"])}</td>'
                    f'<td>{html.escape(e["prediccion"])}</td><td class="n">{number(e.get("rmse_ajuste"))}</td>'
                    f'<td class="n">{number(e.get("rmse_control"))}</td><td>{VERDICT.get(e["status"], e["status"])}</td></tr>')
    rows.append('</table></div>')
    return '\n  '.join(rows)


def replace(path: Path, body: str, marker: str = 'HIPOTESIS') -> None:
    text = path.read_text()
    pattern = re.compile(rf'(<!-- {marker}:INICIO -->).*?(<!-- {marker}:FIN -->)', flags=re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f'{path}: faltan los marcadores {marker}')
    path.write_text(pattern.sub(lambda m: m.group(1) + '\n\n' + body + '\n\n' + m.group(2), text))


def main() -> int:
    experiments = bitacora.load(ROOT / 'docente' / 'plan-b' / 'ensayo')
    if not experiments:
        raise SystemExit('no hay ensayo en docente/plan-b/ensayo/')
    replace(ROOT / 'slides' / 'clase.md', slides(experiments))
    replace(ROOT / 'web' / 'index.html', table_html(experiments))
    # The same run as an animation: frames for the page player and a GIF for the deck.
    rehearsal = ROOT / 'docente' / 'plan-b' / 'ensayo'
    frame_paths = bitacora.frames(experiments, rehearsal / 'corridas' / 'animacion')
    bitacora.write_gif(frame_paths, rehearsal / 'animacion.gif')
    (rehearsal / 'bitacora.html').write_text(bitacora.page(experiments, frame_paths))
    replace(ROOT / 'web' / 'index.html', bitacora.player_html([f'img/loop/{p.name}' for p in frame_paths]), 'ANIMACION')
    print(f'{len(experiments)} experimentos en slides y página, {len(frame_paths)} cuadros de animación')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
