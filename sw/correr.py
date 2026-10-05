"""Run OPM Flow on a deck, from a container pinned by digest or from a native binary.

    FLOW=/usr/bin/flow     use an installed binary instead of the container
    CONTENEDOR=docker      use docker instead of podman
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

IMAGE = ('docker.io/openporousmedia/opmreleases'
         '@sha256:db8865d7c80440513c8c73df7ed385a3b7d2e055a0ef95f7662ec06ef6a6b3a9')   # 2026.04, CPU
TIMEOUT = 60   # seconds; an initialization takes about one


class FlowError(RuntimeError):
    pass


def command(deck: Path, out_dir: Path) -> list[str]:
    flow_args = ['--output-dir={}', '--enable-ecl-output=true', '--threads-per-process=1']
    native = os.environ.get('FLOW')
    if native:
        return [native, str(deck), *(a.format(out_dir) for a in flow_args)]
    runtime = os.environ.get('CONTENEDOR', 'podman')
    if shutil.which(runtime) is None:
        raise FlowError(f'no encuentro {runtime}: instalarlo o definir FLOW con la ruta a un flow nativo')
    cmd = [runtime, 'run', '--rm', '--pull=never', '--network=none',
           '--cap-drop=ALL', '--security-opt=no-new-privileges',
           '--user', f'{os.getuid()}:{os.getgid()}']
    if runtime == 'podman':
        cmd.append('--userns=keep-id')
    cmd += ['-v', f'{deck.parent}:/input:ro,Z', '-v', f'{out_dir}:/output:Z', '-w', '/input',
            '--entrypoint=flow', IMAGE, f'/input/{deck.name}', *(a.format('/output') for a in flow_args)]
    return cmd


def run_flow(deck: Path, out_dir: Path, timeout: int = TIMEOUT) -> float:
    """Run the deck and return the wall time in seconds. Flow's console goes to out_dir/flow.log."""
    deck, out_dir = deck.resolve(), out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / 'flow.log'
    t0 = time.monotonic()
    try:
        with open(log, 'w') as fh:
            proc = subprocess.run(command(deck, out_dir), stdout=fh, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise FlowError(f'flow no terminó en {timeout} s') from e
    seconds = time.monotonic() - t0
    if proc.returncode != 0 or not (out_dir / f'{deck.stem}.UNRST').exists():
        tail = '\n'.join(log.read_text(errors='replace').splitlines()[-25:])
        raise FlowError(f'flow terminó con código {proc.returncode}. Final de {log}:\n{tail}')
    return seconds
