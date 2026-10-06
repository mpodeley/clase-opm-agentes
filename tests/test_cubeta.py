import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'web'))

import cubeta  # noqa: E402


def tilted_block() -> np.ndarray:
    """A base that deepens to the east, 1 m per node, 20 nodes wide."""
    return np.tile(3000.0 + np.arange(20.0), (15, 1))


def test_an_open_slope_holds_no_water():
    depth = tilted_block()
    level = cubeta.spill_level(depth, np.zeros(depth.shape, dtype=bool))
    assert np.allclose(level, depth)


def test_a_bowl_fills_to_its_rim():
    depth = np.full((21, 21), 3000.0)
    i, j = np.indices(depth.shape)
    bowl = np.hypot(i - 10, j - 10) < 6
    depth[bowl] = 3000.0 + 12.0 - 2.0 * np.hypot(i - 10, j - 10)[bowl]
    level = cubeta.spill_level(depth, np.zeros(depth.shape, dtype=bool))
    assert level[10, 10] == 3000.0 and depth[10, 10] == 3012.0


def test_a_sealing_step_turns_a_slope_into_a_trap():
    """A block that dips east into a fault: open, the water runs off; sealed, it stands up to the west rim."""
    depth = tilted_block()
    depth[:, 16:] = 3300.0                     # the downthrown side
    walls = np.zeros(depth.shape, dtype=bool)
    walls[0, :] = walls[-1, :] = True          # the block is closed to the north and to the south
    open_fault = cubeta.spill_level(depth, walls)
    assert np.isclose(open_fault[8, 14], depth[8, 14])           # drains across the step
    sealed = walls.copy()
    sealed[:, 15] = True
    level = cubeta.spill_level(depth, sealed)
    assert np.isclose(level[8, 14], 3000.0)                      # trapped up to the shallow west edge
    assert np.isclose(depth[8, 14] - level[8, 14], 14.0)
