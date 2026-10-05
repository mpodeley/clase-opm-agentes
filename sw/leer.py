"""Read the initial state Flow wrote."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import resfo

from sw.modelo import DECK_NAME


def initial_swat(out_dir: Path, n_cells: int) -> np.ndarray:
    """Water saturation at report step 0, one value per cell in deck order."""
    for entry in resfo.lazy_read(out_dir / f'{DECK_NAME}.UNRST'):
        if entry.read_keyword().strip() == 'SWAT':
            swat = np.array(entry.read_array(), dtype=float)
            break
    else:
        raise ValueError('el restart no tiene SWAT')
    if len(swat) != n_cells:
        raise ValueError(f'el restart tiene {len(swat)} celdas activas y el modelo {n_cells}')
    return swat
