from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


PLAYER_ONE = 1
PLAYER_TWO = -1
EMPTY = 0


@dataclass(frozen=True)
class Move:
    row: int
    col: int
    player: int


@dataclass
class ConnectFour:
    """Connect Four state with a bot-friendly API."""

    rows: int = 6
    cols: int = 7
    connect_n: int = 4
    board: List[List[int]] = field(default_factory=list)
    current_player: int = PLAYER_ONE
    winner: Optional[int] = None
    history: List[Move] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.board:
            self.board = [[EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        if len(self.board) != self.rows or any(len(row) != self.cols for row in self.board):
            raise ValueError("Board dimensions do not match rows/cols")

    @property
    def moves_played(self) -> int:
        return len(self.history)

    @property
    def max_moves(self) -> int:
        return self.rows * self.cols

    def clone(self) -> "ConnectFour":
        return ConnectFour(
            rows=self.rows,
            cols=self.cols,
            connect_n=self.connect_n,
            board=[row[:] for row in self.board],
            current_player=self.current_player,
            winner=self.winner,
            history=self.history[:],
        )

    def snapshot(self) -> Tuple[Tuple[int, ...], ...]:
        return tuple(tuple(row) for row in self.board)

    def legal_moves(self) -> List[int]:
        if self.winner is not None:
            return []
        return [c for c in range(self.cols) if self.board[0][c] == EMPTY]

    def is_terminal(self) -> bool:
        return self.winner is not None

    def drop(self, col: int) -> Move:
        if self.winner is not None:
            raise ValueError("Game is already finished")
        if col < 0 or col >= self.cols:
            raise ValueError(f"Column out of range: {col}")

        row = self._find_open_row(col)
        if row is None:
            raise ValueError(f"Column is full: {col}")

        move = Move(row=row, col=col, player=self.current_player)
        self.board[row][col] = self.current_player
        self.history.append(move)

        if self._is_winning_move(move):
            self.winner = move.player
        elif self.moves_played >= self.max_moves:
            self.winner = 0
        else:
            self.current_player = -self.current_player
        return move

    def as_ascii(self) -> str:
        glyph = {PLAYER_ONE: "X", PLAYER_TWO: "O", EMPTY: "."}
        lines = [" ".join(str(c) for c in range(self.cols))]
        for row in self.board:
            lines.append(" ".join(glyph[cell] for cell in row))
        return "\n".join(lines)

    def _find_open_row(self, col: int) -> Optional[int]:
        for row in range(self.rows - 1, -1, -1):
            if self.board[row][col] == EMPTY:
                return row
        return None

    def _is_winning_move(self, move: Move) -> bool:
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))
        for d_row, d_col in directions:
            total = 1
            total += self._count_direction(move, d_row, d_col)
            total += self._count_direction(move, -d_row, -d_col)
            if total >= self.connect_n:
                return True
        return False

    def _count_direction(self, move: Move, d_row: int, d_col: int) -> int:
        count = 0
        row = move.row + d_row
        col = move.col + d_col
        while 0 <= row < self.rows and 0 <= col < self.cols and self.board[row][col] == move.player:
            count += 1
            row += d_row
            col += d_col
        return count
