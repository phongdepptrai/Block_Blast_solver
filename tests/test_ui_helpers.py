import cv2
import numpy as np
import pytest
from app import draw_solution_step, draw_block_preview

def test_draw_block_preview():
    # Test 2x2 block
    block = [[1, 1], [1, 1]]
    img = draw_block_preview(block)
    assert img is not None
    assert img.shape[0] == 60 # 2 * 30
    assert img.shape[1] == 60
    assert img.shape[2] == 3

def test_draw_solution_step():
    # Create dummy image 100x100
    base_img = np.zeros((100, 100, 3), dtype=np.uint8)

    board_info = {
        'x': 10, 'y': 10,
        'cell_w': 10, 'cell_h': 10
    }

    block = [[1]] # 1x1 block

    # Draw at r=0, c=0 -> should be at 10,10
    res_img = draw_solution_step(base_img, board_info, block, 0, 0, 1)

    assert res_img is not None
    assert res_img.shape == base_img.shape
    # Check if pixels changed (simple check)
    # The center of the drawn cell should not be pure black (0) anymore due to green overlay
    # Center of 10,10 to 20,20 is 15,15
    # Original is 0, overlay is green, so result > 0
    assert np.any(res_img[15, 15] > 0)
