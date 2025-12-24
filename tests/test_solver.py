import pytest
from solver import BlockBlastSolver

@pytest.fixture
def solver_instance():
    return BlockBlastSolver()

def test_can_place(solver_instance):
    board = [[0]*8 for _ in range(8)]
    block = [[1, 1], [1, 1]] # 2x2

    # Valid placement
    assert solver_instance.can_place(board, block, 0, 0) == True

    # Out of bounds
    assert solver_instance.can_place(board, block, 7, 7) == False

    # Overlap
    board[0][0] = 1
    assert solver_instance.can_place(board, block, 0, 0) == False

def test_place_block(solver_instance):
    board = [[0]*8 for _ in range(8)]
    block = [[1]]

    new_board = solver_instance.place_block(board, block, 5, 5)
    assert new_board[5][5] == 1
    assert board[5][5] == 0 # Original should be unchanged

def test_clear_lines(solver_instance):
    board = [[0]*8 for _ in range(8)]
    # Fill row 7
    for c in range(8): board[7][c] = 1

    new_board, score = solver_instance.clear_lines(board)

    assert score == 10
    assert sum(new_board[7]) == 0 # Row cleared

def test_solve_simple(solver_instance):
    board = [[0]*8 for _ in range(8)]
    blocks = [
        [[1]],
        [[1]]
    ]

    solution = solver_instance.solve(board, blocks)
    assert len(solution) == 2

def test_solve_impossible(solver_instance):
    board = [[1]*8 for _ in range(8)] # Full board
    board[0][0] = 0 # One spot

    blocks = [
        [[1, 1]] # 1x2 block, won't fit
    ]

    solution = solver_instance.solve(board, blocks)
    assert len(solution) == 0
