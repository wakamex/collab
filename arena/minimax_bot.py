from __future__ import annotations

import random
from dataclasses import dataclass

from .game import ConnectFour, PLAYER_ONE, PLAYER_TWO, EMPTY


@dataclass
class MinimaxBot:
    """Minimax with alpha-beta pruning and a positional heuristic."""

    name: str = "minimax"
    depth: int = 6

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")

        # Single move shortcut
        if len(legal) == 1:
            return legal[0]

        best_score = float("-inf")
        best_moves: list[int] = []

        for col in legal:
            sim = game.clone()
            sim.drop(col)
            score = self._alphabeta(sim, self.depth - 1, float("-inf"), float("inf"), False, player)
            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)

        return rng.choice(best_moves)

    def _alphabeta(
        self,
        game: ConnectFour,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        root_player: int,
    ) -> float:
        if game.winner is not None:
            return self._terminal_score(game.winner, root_player, depth)
        if depth == 0:
            return self._evaluate(game, root_player)

        legal = game.legal_moves()
        # Search center columns first for better pruning
        center = game.cols // 2
        legal.sort(key=lambda c: abs(c - center))

        if maximizing:
            value = float("-inf")
            for col in legal:
                sim = game.clone()
                sim.drop(col)
                value = max(value, self._alphabeta(sim, depth - 1, alpha, beta, False, root_player))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float("inf")
            for col in legal:
                sim = game.clone()
                sim.drop(col)
                value = min(value, self._alphabeta(sim, depth - 1, alpha, beta, True, root_player))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def _terminal_score(self, winner: int, root_player: int, depth: int) -> float:
        if winner == 0:
            return 0.0
        # Prefer faster wins / slower losses
        bonus = depth + 1
        return (10_000 + bonus) if winner == root_player else -(10_000 + bonus)

    def _evaluate(self, game: ConnectFour, root_player: int) -> float:
        score = 0.0
        board = game.board
        rows, cols, n = game.rows, game.cols, game.connect_n

        # Center column preference
        center = cols // 2
        for r in range(rows):
            if board[r][center] == root_player:
                score += 3
            elif board[r][center] == -root_player:
                score -= 3

        # Evaluate all windows of length connect_n
        for r in range(rows):
            for c in range(cols):
                # Horizontal
                if c + n <= cols:
                    score += self._score_window(
                        [board[r][c + i] for i in range(n)], root_player
                    )
                # Vertical
                if r + n <= rows:
                    score += self._score_window(
                        [board[r + i][c] for i in range(n)], root_player
                    )
                # Diagonal down-right
                if r + n <= rows and c + n <= cols:
                    score += self._score_window(
                        [board[r + i][c + i] for i in range(n)], root_player
                    )
                # Diagonal up-right
                if r - n + 1 >= 0 and c + n <= cols:
                    score += self._score_window(
                        [board[r - i][c + i] for i in range(n)], root_player
                    )

        return score

    @staticmethod
    def _score_window(window: list[int], player: int) -> float:
        own = window.count(player)
        opp = window.count(-player)
        empty = window.count(EMPTY)

        if own > 0 and opp > 0:
            return 0.0  # contested window

        if own == 3 and empty == 1:
            return 50.0
        if own == 2 and empty == 2:
            return 5.0
        if opp == 3 and empty == 1:
            return -40.0
        if opp == 2 and empty == 2:
            return -3.0
        return 0.0
