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
        # Combo logic: if >1 line, bonus points.
        num_lines = len(rows_to_clear) + len(cols_to_clear)
        score = num_lines * 10
        if num_lines > 1:
            score += num_lines * 5 # Bonus

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

    def count_empty_cells(self, board):
        """Counts the number of empty cells (0s) on the board."""
        return sum(row.count(0) for row in board)

    def solve(self, board, blocks, strategy="score"):
        """
        Finds the best sequence of moves.
        strategies:
          - "score": Maximize total score.
          - "survival": Maximize empty space (minimize filled cells) after all moves.

        Returns: list_of_moves
        move = {'block_index': int, 'r': int, 'c': int}
        """

        # We need to maximize a "fitness" metric based on strategy
        # For "score": fitness = current_score
        # For "survival": fitness = current_score + (empty_cells * huge_weight)
        # Actually, survival should just prioritize empty cells, but score is a good tiebreaker.

        self.best_global_fitness = -1e9
        self.best_global_path = []

        def calculate_fitness(current_score, current_board):
            if strategy == "score":
                return current_score
            elif strategy == "survival":
                # Primary: Empty cells (more is better). Max empty is 64.
                # Secondary: Score.
                empty = self.count_empty_cells(current_board)
                return empty * 1000 + current_score
            return current_score

        def dfs(current_board, available_indices, current_score, path):
            if not available_indices:
                fitness = calculate_fitness(current_score, current_board)
                if fitness > self.best_global_fitness:
                    self.best_global_fitness = fitness
                    self.best_global_path = list(path)
                return

            valid_move_found = False

            for i in available_indices:
                block = blocks[i]

                # Heuristic optimization: If survival mode, maybe prioritize clearing lines immediately?
                # The DFS does exhaust search so it will find it.

                for r in range(self.rows - len(block) + 1):
                    for c in range(self.cols - len(block[0]) + 1):
                        if self.can_place(current_board, block, r, c):
                            valid_move_found = True

                            # Execute move
                            temp_board = self.place_block(current_board, block, r, c)
                            placement_points = self.count_cells(block)

                            # Clear lines
                            next_board, line_points = self.clear_lines(temp_board)

                            new_score = current_score + placement_points + line_points

                            # Recurse
                            remaining_indices = [idx for idx in available_indices if idx != i]

                            dfs(next_board, remaining_indices, new_score, path + [{'block_idx': i, 'r': r, 'c': c, 'score_gain': placement_points + line_points}])

            # If we couldn't place this block, it's a dead end for this path (Game Over equivalent)
            # However, in "survival" mode, maybe we placed 2 blocks and the 3rd failed.
            # We should still record the result of the 2 blocks if it's better than nothing.
            if not valid_move_found or (available_indices and not valid_move_found):
                fitness = calculate_fitness(current_score, current_board)
                if fitness > self.best_global_fitness:
                    self.best_global_fitness = fitness
                    self.best_global_path = list(path)

        dfs(board, list(range(len(blocks))), 0, [])

        return self.best_global_path

def format_solution(moves):
    result = []
    for m in moves:
        result.append(f"Block {m['block_idx']}: Place at Row {m['r']}, Col {m['c']}")
    return result

if __name__ == "__main__":
    s = BlockBlastSolver()
    board = [[0]*8 for _ in range(8)]
    # Create a situation where clearing a line is possible but maybe not optimal for survival?
    # Hard to construct simple case, but let's test basic functionality

    blocks = [
        [[1]],
        [[1, 1]]
    ]

    path = s.solve(board, blocks, strategy="score")
    print("Score Strategy Path:", path)

    path_survival = s.solve(board, blocks, strategy="survival")
    print("Survival Strategy Path:", path_survival)
