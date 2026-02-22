from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .game import ConnectFour, EMPTY


@dataclass
class NegamaxBot:
    """Enhanced alpha-beta with transposition table and iterative deepening.

    Builds on the proven MinimaxBot approach but adds:
    - Transposition table to avoid re-searching identical positions
    - Iterative deepening from 1 to max_depth for move-ordering info
    - Killer move heuristic for better pruning
    - Double-threat detection before search
    - Deeper default search (8 vs minimax's 6)
    """

    name: str = "negamax"
    max_depth: int = 8

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")
        if len(legal) == 1:
            return legal[0]

        # Immediate win
        for col in legal:
            sim = game.clone()
            sim.drop(col)
            if sim.winner == player:
                return col

        # Immediate block
        for col in legal:
            sim = game.clone()
            sim.current_player = -player
            sim.drop(col)
            if sim.winner == -player:
                return col

        # Double-threat: find a move that creates 2+ ways to win
        dt = self._find_double_threat(game, player)
        if dt is not None:
            return dt

        # Search
        tt: Dict[Tuple, Tuple[float, int, int, int]] = {}
        killers: List[List[int]] = [[] for _ in range(self.max_depth + 2)]
        center = game.cols // 2
        col_order = sorted(range(game.cols), key=lambda c: abs(c - center))

        best_move = legal[len(legal) // 2]

        for depth in range(1, self.max_depth + 1):
            move, score = self._id_search(game, player, depth, rng, tt, killers, col_order)
            if move is not None:
                best_move = move
                if abs(score) > 90_000:
                    break

        return best_move

    def _find_double_threat(self, game: ConnectFour, player: int) -> Optional[int]:
        """Find a move creating 2+ simultaneous winning threats."""
        for col in game.legal_moves():
            sim = game.clone()
            sim.drop(col)
            if sim.winner is not None:
                continue
            threats = 0
            for nc in sim.legal_moves():
                sim2 = sim.clone()
                sim2.current_player = player
                sim2.drop(nc)
                if sim2.winner == player:
                    threats += 1
                    if threats >= 2:
                        return col
        return None

    def _id_search(
        self, game: ConnectFour, player: int, depth: int, rng: random.Random,
        tt: Dict, killers: List[List[int]], col_order: List[int],
    ) -> Tuple[Optional[int], float]:
        legal = game.legal_moves()
        center = game.cols // 2
        ordered = self._order_moves(legal, game.snapshot(), tt, killers, depth, col_order)

        best_score = float("-inf")
        best_moves: List[int] = []

        for col in ordered:
            sim = game.clone()
            sim.drop(col)
            score = self._alphabeta(
                sim, depth - 1, float("-inf"), float("inf"),
                False, player, tt, killers, col_order
            )
            if score > best_score:
                best_score = score
                best_moves = [col]
            elif score == best_score:
                best_moves.append(col)

        if not best_moves:
            return None, 0.0
        return rng.choice(best_moves), best_score

    def _alphabeta(
        self, game: ConnectFour, depth: int,
        alpha: float, beta: float, maximizing: bool, root_player: int,
        tt: Dict, killers: List[List[int]], col_order: List[int],
    ) -> float:
        if game.winner is not None:
            return self._terminal_score(game.winner, root_player, depth)
        if depth == 0:
            return self._evaluate(game, root_player)

        # TT lookup
        snap = game.snapshot()
        tt_entry = tt.get(snap)
        if tt_entry is not None:
            tt_score, tt_depth, tt_flag, _tt_move = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score
                elif tt_flag == 1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 2:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score

        legal = game.legal_moves()
        ordered = self._order_moves(legal, snap, tt, killers, depth, col_order)

        orig_alpha = alpha
        best_move = ordered[0] if ordered else 0

        if maximizing:
            value = float("-inf")
            for col in ordered:
                sim = game.clone()
                sim.drop(col)
                score = self._alphabeta(sim, depth - 1, alpha, beta, False, root_player, tt, killers, col_order)
                if score > value:
                    value = score
                    best_move = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    k = killers[depth]
                    if col not in k:
                        k.insert(0, col)
                        if len(k) > 2:
                            k.pop()
                    break
        else:
            value = float("inf")
            for col in ordered:
                sim = game.clone()
                sim.drop(col)
                score = self._alphabeta(sim, depth - 1, alpha, beta, True, root_player, tt, killers, col_order)
                if score < value:
                    value = score
                    best_move = col
                beta = min(beta, value)
                if alpha >= beta:
                    k = killers[depth]
                    if col not in k:
                        k.insert(0, col)
                        if len(k) > 2:
                            k.pop()
                    break

        # TT store
        if value <= orig_alpha:
            flag = 2  # UPPER
        elif value >= beta:
            flag = 1  # LOWER
        else:
            flag = 0  # EXACT
        tt[snap] = (value, depth, flag, best_move)

        return value

    def _terminal_score(self, winner: int, root_player: int, depth: int) -> float:
        if winner == 0:
            return 0.0
        bonus = depth + 1
        return (10_000 + bonus) if winner == root_player else -(10_000 + bonus)

    def _evaluate(self, game: ConnectFour, root_player: int) -> float:
        score = 0.0
        board = game.board
        rows, cols, n = game.rows, game.cols, game.connect_n
        center = cols // 2

        # Center column
        for r in range(rows):
            if board[r][center] == root_player:
                score += 3
            elif board[r][center] == -root_player:
                score -= 3

        # All windows
        for r in range(rows):
            for c in range(cols):
                if c + n <= cols:
                    score += _score_window(board[r][c], board[r][c+1], board[r][c+2], board[r][c+3], root_player)
                if r + n <= rows:
                    score += _score_window(board[r][c], board[r+1][c], board[r+2][c], board[r+3][c], root_player)
                if r + n <= rows and c + n <= cols:
                    score += _score_window(board[r][c], board[r+1][c+1], board[r+2][c+2], board[r+3][c+3], root_player)
                if r - n + 1 >= 0 and c + n <= cols:
                    score += _score_window(board[r][c], board[r-1][c+1], board[r-2][c+2], board[r-3][c+3], root_player)

        # Threat counting
        own_threats = 0
        opp_threats = 0
        for col in game.legal_moves():
            row = _drop_row(board, col, rows)
            if row is None:
                continue
            board[row][col] = root_player
            if _check_win_at(board, row, col, root_player, rows, cols, n):
                own_threats += 1
            board[row][col] = -root_player
            if _check_win_at(board, row, col, -root_player, rows, cols, n):
                opp_threats += 1
            board[row][col] = EMPTY

        if own_threats >= 2:
            score += 300
        elif own_threats == 1:
            score += 30
        if opp_threats >= 2:
            score -= 250
        elif opp_threats == 1:
            score -= 20

        return score

    def _order_moves(
        self, legal: List[int], snap: Tuple, tt: Dict,
        killers: List[List[int]], depth: int, col_order: List[int],
    ) -> List[int]:
        tt_entry = tt.get(snap)
        tt_move = tt_entry[3] if tt_entry else -1
        k = killers[depth] if depth < len(killers) else []

        result: List[int] = []
        added: set = set()

        if tt_move in legal:
            result.append(tt_move)
            added.add(tt_move)
        for km in k:
            if km in legal and km not in added:
                result.append(km)
                added.add(km)
        for c in col_order:
            if c in legal and c not in added:
                result.append(c)
        return result


def _score_window(a: int, b: int, c: int, d: int, player: int) -> float:
    own = (a == player) + (b == player) + (c == player) + (d == player)
    opp = (a == -player) + (b == -player) + (c == -player) + (d == -player)
    if own and opp:
        return 0.0
    if own == 3:
        return 50.0
    if own == 2 and not opp:
        return 5.0
    if opp == 3:
        return -40.0
    if opp == 2 and not own:
        return -3.0
    return 0.0


def _drop_row(board: List[List[int]], col: int, rows: int) -> Optional[int]:
    for row in range(rows - 1, -1, -1):
        if board[row][col] == EMPTY:
            return row
    return None


def _check_win_at(
    board: List[List[int]], row: int, col: int, player: int,
    rows: int, cols: int, n: int,
) -> bool:
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        r, c = row - dr, col - dc
        while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= n:
            return True
    return False
