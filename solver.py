import copy

class BlockBlastSolver:
    def __init__(self):
        self.rows = 8
        self.cols = 8

    def can_place(self, board, block, start_r, start_c):
        """Checks if a block can be placed at the given coordinates."""
        block_h = len(block)
        block_w = len(block[0])

        if start_r + block_h > self.rows or start_c + block_w > self.cols:
            return False

        for r in range(block_h):
            for c in range(block_w):
                if block[r][c] == 1 and board[start_r + r][start_c + c] == 1:
                    return False
        return True

    def place_block(self, board, block, start_r, start_c):
        """Places a block on the board and returns the new board."""
        new_board = [row[:] for row in board]
        block_h = len(block)
        block_w = len(block[0])

        for r in range(block_h):
            for c in range(block_w):
                if block[r][c] == 1:
                    new_board[start_r + r][start_c + c] = 1
        return new_board

    def clear_lines(self, board):
        """Clears full rows and columns, returns new board and score increase."""
        rows_to_clear = []
        cols_to_clear = []

        # Identify full rows
        for r in range(self.rows):
            if all(board[r]):
                rows_to_clear.append(r)

        # Identify full cols
        for c in range(self.cols):
            if all(board[r][c] for r in range(self.rows)):
                cols_to_clear.append(c)

        if not rows_to_clear and not cols_to_clear:
            return board, 0

        # Calculate score (simplified logic: 10 pts per line)
        # Real game has combos, but this is a good heuristic
        score = (len(rows_to_clear) + len(cols_to_clear)) * 10

        # Create new board with lines cleared
        new_board = [row[:] for row in board]

        for r in rows_to_clear:
            for c in range(self.cols):
                new_board[r][c] = 0

        for c in cols_to_clear:
            for r in range(self.rows):
                new_board[r][c] = 0

        return new_board, score

    def count_cells(self, block):
        return sum(sum(row) for row in block)

    def solve(self, board, blocks):
        """
        Finds the best sequence of moves.
        Returns: (max_score, list_of_moves)
        move = {'block_index': int, 'r': int, 'c': int}
        """

        best_score = -1
        best_path = []

        # block_indices = list(range(len(blocks)))
        # We need to try all permutations of blocks?
        # The game allows placing available blocks in any order.
        # Yes, order matters.

        # State: (current_board, available_block_indices, current_score, path)
        stack = [(board, list(range(len(blocks))), 0, [])]

        # To avoid infinite loops or too deep recursion, we can just use recursion
        # But let's stick to a recursive helper for clarity

        self.best_global_score = -1
        self.best_global_path = []

        def dfs(current_board, available_indices, current_score, path):
            if not available_indices:
                if current_score > self.best_global_score:
                    self.best_global_score = current_score
                    self.best_global_path = list(path)
                return

            # Optimization: If we can't beat the best score even with perfect clears?
            # Hard to estimate.

            # Optimization: Try to find ANY valid move first.
            can_move = False

            for i in available_indices:
                block = blocks[i]

                # Try all positions
                # Heuristic: Optimization?
                # For now, brute force.

                valid_placement_found_for_this_block = False

                for r in range(self.rows - len(block) + 1):
                    for c in range(self.cols - len(block[0]) + 1):
                        if self.can_place(current_board, block, r, c):
                            valid_placement_found_for_this_block = True

                            # Execute move
                            temp_board = self.place_block(current_board, block, r, c)
                            placement_points = self.count_cells(block)

                            # Clear lines
                            next_board, line_points = self.clear_lines(temp_board)

                            new_score = current_score + placement_points + line_points

                            # Recurse
                            remaining_indices = [idx for idx in available_indices if idx != i]

                            dfs(next_board, remaining_indices, new_score, path + [{'block_idx': i, 'r': r, 'c': c, 'score_gain': placement_points + line_points}])

            # If no move was possible for ANY remaining block, the game ends (or partial solution)
            # We should record this score
            if current_score > self.best_global_score:
                self.best_global_score = current_score
                self.best_global_path = list(path)

        dfs(board, list(range(len(blocks))), 0, [])

        return self.best_global_path

def format_solution(moves):
    result = []
    for m in moves:
        result.append(f"Block {m['block_idx']}: Place at Row {m['r']}, Col {m['c']}")
    return result

if __name__ == "__main__":
    # Test with dummy data
    s = BlockBlastSolver()
    board = [[0]*8 for _ in range(8)]
    # Create a near-full row for testing
    for c in range(7): board[7][c] = 1

    blocks = [
        [[1]], # 1x1
        [[1, 1]] # 1x2
    ]

    path = s.solve(board, blocks)
    print(path)
