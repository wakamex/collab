from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from .game import ConnectFour


class Bot(Protocol):
    """Bot contract for all strategies."""

    name: str

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        """Return a legal column index."""


@dataclass
class RandomBot:
    name: str = "random"

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")
        return rng.choice(legal)


@dataclass
class GreedyBot:
    name: str = "greedy"

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")

        win_move = self._find_immediate_win(game, player)
        if win_move is not None:
            return win_move

        block_move = self._find_immediate_win(game, -player)
        if block_move is not None:
            return block_move

        center = game.cols // 2
        ordered = sorted(legal, key=lambda col: (abs(col - center), col))
        best_distance = abs(ordered[0] - center)
        tied = [col for col in ordered if abs(col - center) == best_distance]
        return rng.choice(tied)

    def _find_immediate_win(self, game: ConnectFour, player: int) -> int | None:
        for col in game.legal_moves():
            sim = game.clone()
            sim.current_player = player
            sim.drop(col)
            if sim.winner == player:
                return col
        return None
