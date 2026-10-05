"""The loop's logbook: every experiment with the hypothesis written before it ran.

    uv run bitacora.py                 # writes bitacora.html next to results.tsv
    uv run bitacora.py --tabla-md      # prints the experiments as a Markdown table
    uv run bitacora.py --animacion     # also writes animacion.gif and its frames

The animation has one frame per experiment: the hypothesis on top, the logs and the J function
below, and the error curve growing on the right. bitacora.html plays the same frames.

Sources: corridas/exp-NN-<commit>/registro.json (commit message and metrics, written by
`evaluar.py --experimento`) and results.tsv (status and the reading after the run).
The commit message carries the hypothesis on its first line, then `mecanismo:` and `prediccion:`.
"""
from __future__ import annotations

import argparse
import base64
import csv
import difflib
import html
import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUS = {'keep': 'conservado', 'discard': 'descartado', 'crash': 'falló'}


def parse_message(message: str) -> dict[str, str]:
    lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
    out = {'hipotesis': lines[0] if lines else '', 'mecanismo': '', 'prediccion': ''}
    for line in lines[1:]:
        m = re.match(r'(mecanismo|predicci[oó]n)\s*:\s*(.*)', line, flags=re.IGNORECASE)
        if m:
            out['mecanismo' if m.group(1).lower().startswith('m') else 'prediccion'] = m.group(2)
    return out


def load(root: Path) -> list[dict]:
    """One dict per experiment, in the order they ran."""
    status = {}
    tsv = root / 'results.tsv'
    if tsv.exists():
        with open(tsv, newline='') as fh:
            for row in csv.DictReader(fh, delimiter='\t'):
                status[row.get('commit', '').strip()] = row
    experiments, kept = [], None
    for folder in sorted((root / 'corridas').glob('exp-*')):
        record_file = folder / 'registro.json'
        if not record_file.exists():
            continue
        record = json.loads(record_file.read_text())
        row = status.get(record['commit'], {})
        e = {'n': len(experiments) + 1, 'folder': folder, **record, **parse_message(record.get('mensaje', '')),
             'status': (row.get('status') or '').strip() or 'sin anotar', 'lectura': (row.get('lectura') or '').strip()}
        fragment = (folder / 'fragmento.txt').read_text() if (folder / 'fragmento.txt').exists() else ''
        e['diff'] = '\n'.join(line for line in difflib.unified_diff(
            (kept or '').splitlines(), fragment.splitlines(), lineterm='', n=0)
            if not line.startswith(('---', '+++', '@@'))) if kept is not None else ''
        if e['status'] == 'keep' or kept is None:
            kept = fragment
        experiments.append(e)
    return experiments


def number(value) -> str:
    return f'{value:.4f}' if isinstance(value, float) else '—'


def table_markdown(experiments: list[dict]) -> str:
    lines = ['| N.º | Hipótesis | Predicción | RMSE de ajuste | RMSE de control | Parámetros | Resultado |',
             '| ---: | --- | --- | ---: | ---: | ---: | --- |']
    for e in experiments:
        lines.append(f"| {e['n']} | {e['hipotesis']} | {e['prediccion'] or '—'} | {number(e.get('rmse_ajuste'))} | "
                     f"{number(e.get('rmse_control'))} | {e.get('n_parametros', '—')} | {STATUS.get(e['status'], e['status'])} |")
    return '\n'.join(lines)


def chart_svg(experiments: list[dict]) -> str:
    """Fit and control error per experiment. Filled marks were kept, hollow ones discarded."""
    runs = [e for e in experiments if isinstance(e.get('rmse_ajuste'), float)]
    if not runs:
        return ''
    w, h, left, right, top, bottom = 860, 300, 56, 150, 18, 38
    values = [e[k] for e in runs for k in ('rmse_ajuste', 'rmse_control')]
    lo, hi = min(values) * 0.92, max(values) * 1.05
    x = lambda n: left + (w - left - right) * (n - 1) / max(len(experiments) - 1, 1)   # noqa: E731
    y = lambda v: top + (h - top - bottom) * (hi - v) / (hi - lo)                       # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Error de ajuste y de control por experimento">']
    for i in range(5):
        v = lo + (hi - lo) * i / 4
        out.append(f'<line x1="{left}" x2="{w - right}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>'
                   f'<text x="{left - 8}" y="{y(v) + 4:.1f}" class="tick" text-anchor="end">{v:.3f}</text>')
    for e in experiments:
        out.append(f'<text x="{x(e["n"]):.1f}" y="{h - 14}" class="tick" text-anchor="middle">{e["n"]}</text>')
    out.append(f'<text x="{(left + w - right) / 2:.0f}" y="{h - 1}" class="tick" text-anchor="middle">experimento</text>')
    for key, cls, label in (('rmse_control', 'control', 'control (F-11 B)'), ('rmse_ajuste', 'fit', 'ajuste (5 pozos)')):
        best, points = None, []
        for e in runs:   # the staircase of the kept cases
            if e['status'] == 'keep' or best is None:
                best = e[key]
            points.append(f'{x(e["n"]):.1f},{y(best):.1f}')
        out.append(f'<polyline points="{" ".join(points)}" class="line {cls}"/>')
        for e in runs:
            hollow = '' if e['status'] == 'keep' else ' hollow'
            out.append(f'<circle cx="{x(e["n"]):.1f}" cy="{y(e[key]):.1f}" r="5" class="mark {cls}{hollow}">'
                       f'<title>{e["n"]}. {html.escape(e["hipotesis"])} — {label}: {e[key]:.4f} '
                       f'({STATUS.get(e["status"], e["status"])})</title></circle>')
        out.append(f'<text x="{w - right + 12}" y="{y(best) + 4:.1f}" class="label">{label}</text>')
    out.append('</svg>')
    return ''.join(out)



def frames(experiments: list[dict], out: Path) -> list[Path]:
    """One 16:9 frame per experiment that ran: hypothesis, figure of the run, error so far."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    ink, muted, surface, grid = '#0b0b0b', '#52514e', '#fcfcfb', '#e1e0d9'
    colours = {'keep': '#147a5f', 'discard': '#8a6412', 'crash': '#8a6412'}
    fit_colour, control_colour = '#2a78d6', '#4a3aa7'
    runs = [e for e in experiments if isinstance(e.get('rmse_ajuste'), float) and (e['folder'] / 'perfil.png').exists()]
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.png'):
        old.unlink()
    values = [e[k] for e in runs for k in ('rmse_ajuste', 'rmse_control')]
    paths = []
    for i, e in enumerate(runs):
        fig = plt.figure(figsize=(16, 9), facecolor=surface)
        fig.text(0.035, 0.955, f'Experimento {e["n"]} de {len(experiments)}', fontsize=15, color=muted, va='top')
        fig.text(0.215, 0.955, STATUS.get(e['status'], e['status']).upper(), fontsize=13, va='top', fontweight='bold',
                 color=colours.get(e['status'], muted))
        title = textwrap.wrap(e['hipotesis'], 84)[:3]
        fig.text(0.035, 0.918, '\n'.join(title), fontsize=17, color=ink, va='top', linespacing=1.25)
        detail = [('Mecanismo', e['mecanismo']), ('Predicción', e['prediccion']),
                  ('Resultado', f'ajuste {e["rmse_ajuste"]:.4f} · control {e["rmse_control"]:.4f} · '
                                f'{e.get("n_parametros", "—")} parámetros'), ('Lectura', e['lectura'])]
        y = 0.918 - 0.039 * len(title) - 0.014
        for label, text in detail:
            if not text:
                continue
            lines = textwrap.wrap(text, 104)
            wrapped = lines[:2]
            if len(lines) > 2:
                wrapped[-1] = wrapped[-1][:100].rstrip() + ' …'
            fig.text(0.035, y, label, fontsize=11, color=muted, va='top')
            fig.text(0.105, y, '\n'.join(wrapped), fontsize=11, color=ink, va='top', linespacing=1.3)
            y -= 0.025 * len(wrapped) + 0.007

        ax = fig.add_axes([0.775, 0.685, 0.20, 0.245], facecolor=surface)
        for key, colour, label in (('rmse_control', control_colour, 'control'), ('rmse_ajuste', fit_colour, 'ajuste')):
            best, stairs = None, []
            for r in runs[:i + 1]:
                if r['status'] == 'keep' or best is None:
                    best = r[key]
                stairs.append(best)
            ax.plot([r['n'] for r in runs[:i + 1]], stairs, color=colour, linewidth=2)
            for r in runs[:i + 1]:
                ax.plot(r['n'], r[key], 'o', ms=7 if r is e else 5, color=colour,
                        markerfacecolor=colour if r['status'] == 'keep' else surface, markeredgewidth=1.6)
            ax.plot([], [], color=colour, linewidth=2, label=label)
        ax.set_xlim(0.5, runs[-1]['n'] + 0.3)
        ax.set_ylim(min(values) * 0.9, max(values) * 1.16)
        ax.set_xticks([r['n'] for r in runs])
        ax.tick_params(colors=muted, labelsize=9, length=0)
        ax.grid(True, color=grid, linewidth=0.6)
        for side in ('top', 'right', 'left', 'bottom'):
            ax.spines[side].set_visible(False)
        ax.legend(loc='upper right', frameon=False, fontsize=9.5, labelcolor=muted, ncols=2, handlelength=1.2)
        ax.set_title('RMSE por experimento', fontsize=10.5, color=ink, loc='left')

        image_ax = fig.add_axes([0.13, 0.0, 0.74, 0.615])
        image_ax.imshow(plt.imread(e['folder'] / 'perfil.png'))
        image_ax.axis('off')
        path = out / f'{i + 1:02d}.png'
        fig.savefig(path, dpi=100, facecolor=surface)
        plt.close(fig)
        paths.append(path)
    return paths


def write_gif(paths: list[Path], target: Path, seconds: float = 4.0) -> None:
    from PIL import Image
    images = [Image.open(p).convert('P', palette=Image.ADAPTIVE, colors=128) for p in paths]
    images[0].save(target, save_all=True, append_images=images[1:], duration=int(seconds * 1000), loop=0, optimize=True)


PLAYER_CSS = """
.player{border:1px solid var(--border);border-radius:8px;padding:10px;margin:18px 0 28px}
.player img{border:0;border-radius:4px;display:block}
.controls{display:flex;gap:10px;align-items:center;margin-top:8px}
.controls button{font:inherit;padding:5px 12px;border:1px solid var(--border);border-radius:6px;background:var(--panel);color:var(--text);cursor:pointer}
.controls input{flex:1}.controls span{font-variant-numeric:tabular-nums;color:var(--muted);min-width:64px;text-align:right}
"""

PLAYER_JS = """
(function(){var f=window.FRAMES,i=0,t=null,img=document.getElementById('frame'),r=document.getElementById('pos'),
c=document.getElementById('count'),b=document.getElementById('play');
function show(n){i=(n+f.length)%f.length;img.src=f[i];r.value=i;c.textContent=(i+1)+' de '+f.length}
function stop(){clearInterval(t);t=null;b.textContent='Reproducir'}
b.onclick=function(){if(t){stop()}else{b.textContent='Pausa';t=setInterval(function(){show(i+1)},3500)}};
document.getElementById('prev').onclick=function(){stop();show(i-1)};
document.getElementById('next').onclick=function(){stop();show(i+1)};
r.max=f.length-1;r.oninput=function(){stop();show(+r.value)};
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'){stop();show(i+1)}if(e.key==='ArrowLeft'){stop();show(i-1)}});
show(0)})();
"""


def player_html(sources: list[str]) -> str:
    """A small frame player. `sources` are image URLs or data URIs, one per experiment."""
    return ('<div class="player"><img id="frame" alt="Cuadro del loop: hipótesis, perfiles, función J y error">'
            '<div class="controls"><button id="prev" aria-label="Anterior">←</button>'
            '<button id="play">Reproducir</button><button id="next" aria-label="Siguiente">→</button>'
            '<input id="pos" type="range" min="0" value="0" aria-label="Experimento"><span id="count"></span></div></div>'
            f'<script>window.FRAMES={json.dumps(sources)};{PLAYER_JS}</script>')


CSS = """
:root{--bg:#fff;--panel:#f4f4f2;--border:#d9dce0;--text:#16181d;--muted:#4a5361;--fit:#2a78d6;--control:#4a3aa7;
--keep:#147a5f;--discard:#8a6412}
@media (prefers-color-scheme:dark){:root{--bg:#0f1012;--panel:#1a1c20;--border:#2c3036;--text:#f4f4f2;--muted:#b4bac4;
--fit:#3987e5;--control:#9085e9;--keep:#3fc79b;--discard:#d9a531}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}
main{max-width:1000px;margin:0 auto;padding:32px 16px 64px}h1{font-size:28px;margin:0 0 4px}h2{font-size:19px;margin:0}
p.lead{color:var(--muted);margin:0 0 20px}svg{width:100%;height:auto}.grid{stroke:var(--border);stroke-width:1}
.tick{font-size:12px;fill:var(--muted)}.label{font-size:13px;fill:var(--text)}.line{fill:none;stroke-width:2}
.line.fit,.mark.fit{stroke:var(--fit)}.line.control,.mark.control{stroke:var(--control)}
.mark{stroke-width:2}.mark.fit{fill:var(--fit)}.mark.control{fill:var(--control)}.mark.hollow{fill:var(--bg)}
article{border-top:1px solid var(--border);padding:18px 0;display:grid;grid-template-columns:1fr 300px;gap:20px}
@media (max-width:760px){article{grid-template-columns:1fr}}
.badge{font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:4px;border:1px solid currentColor}
.keep{color:var(--keep)}.discard,.crash{color:var(--discard)}.head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
dl{margin:10px 0 0;display:grid;grid-template-columns:110px 1fr;gap:4px 12px}dt{color:var(--muted)}dd{margin:0}
pre{background:var(--panel);padding:10px 12px;border-radius:6px;overflow-x:auto;font-size:12.5px;margin:10px 0 0}
img{width:100%;border:1px solid var(--border);border-radius:6px}.num{font-variant-numeric:tabular-nums}
"""


def page(experiments: list[dict], frame_paths: list[Path] | None = None) -> str:
    kept = sum(e['status'] == 'keep' for e in experiments)
    player = ''
    if frame_paths:
        player = player_html(['data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode() for p in frame_paths])
    parts = ['<!doctype html><html lang="es"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Bitácora del loop</title>'
             f'<style>{CSS}{PLAYER_CSS}</style></head><body><main><h1>Bitácora del loop</h1>'
             f'<p class="lead">{len(experiments)} experimentos, {kept} conservados. Marca llena: conservado. '
             'Marca hueca: descartado. La hipótesis y la predicción se escribieron en el commit, antes de correr.</p>',
             player, chart_svg(experiments)]
    for e in experiments:
        image = ''
        if (e['folder'] / 'perfil.png').exists():
            data = base64.b64encode((e['folder'] / 'perfil.png').read_bytes()).decode()
            image = f'<a href="data:image/png;base64,{data}"><img alt="Perfiles del experimento {e["n"]}" src="data:image/png;base64,{data}"></a>'
        result = (f'ajuste {number(e.get("rmse_ajuste"))} · control {number(e.get("rmse_control"))} · '
                  f'{e.get("n_parametros", "—")} parámetros' if 'error' not in e else html.escape(e['error'][:300]))
        diff = f'<pre>{html.escape(e["diff"])}</pre>' if e['diff'] else ''
        parts.append(
            f'<article><div><div class="head"><h2>{e["n"]}. {html.escape(e["hipotesis"])}</h2>'
            f'<span class="badge {e["status"]}">{STATUS.get(e["status"], e["status"])}</span></div><dl>'
            f'<dt>Mecanismo</dt><dd>{html.escape(e["mecanismo"]) or "—"}</dd>'
            f'<dt>Predicción</dt><dd>{html.escape(e["prediccion"]) or "—"}</dd>'
            f'<dt>Resultado</dt><dd class="num">{result}</dd>'
            f'<dt>Lectura</dt><dd>{html.escape(e["lectura"]) or "—"}</dd>'
            f'<dt>Commit</dt><dd class="num">{e["commit"]} · {e.get("hora", "")}</dd></dl>{diff}</div>'
            f'<div>{image}</div></article>')
    parts.append('</main></body></html>')
    return ''.join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description='Arma la bitácora del loop de ajuste.')
    ap.add_argument('--raiz', type=Path, default=ROOT, help='carpeta con results.tsv y corridas/')
    ap.add_argument('--tabla-md', action='store_true')
    ap.add_argument('--animacion', action='store_true', help='escribe animacion.gif y el reproductor en la bitácora')
    args = ap.parse_args()
    experiments = load(args.raiz)
    if args.tabla_md:
        print(table_markdown(experiments))
        return 0
    frame_paths = None
    if args.animacion:
        frame_paths = frames(experiments, args.raiz / 'corridas' / 'animacion')
        if frame_paths:
            write_gif(frame_paths, args.raiz / 'animacion.gif')
    (args.raiz / 'bitacora.html').write_text(page(experiments, frame_paths))
    print(f'bitacora.html: {len(experiments)} experimentos' + (f', animacion.gif: {len(frame_paths)} cuadros' if frame_paths else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
