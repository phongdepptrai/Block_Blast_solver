import numpy as np
import pytest
from app import pad_block_to_5x5, trim_block

def test_pad_block():
    block = [[1, 1], [1, 0]]
    padded = pad_block_to_5x5(block)

    assert len(padded) == 5
    assert len(padded[0]) == 5
    assert padded[0][0] == 1
    assert padded[0][1] == 1
    assert padded[1][1] == 0
    assert padded[4][4] == 0 # Check padding

def test_trim_block():
    # 5x5 block with a 2x2 shape in the middle
    block = np.zeros((5, 5), dtype=int)
    block[2][2] = 1
    block[2][3] = 1
    block[3][2] = 1
    block[3][3] = 1

    trimmed = trim_block(block.tolist())

    assert len(trimmed) == 2
    assert len(trimmed[0]) == 2
    assert trimmed[0][0] == 1
    assert trimmed[1][1] == 1

def test_trim_empty_block():
    block = np.zeros((5, 5), dtype=int).tolist()
    trimmed = trim_block(block)
    # Should return minimal block [[0]] or similar?
    # Logic returns [[0]]
    assert trimmed == [[0]]
