from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .game import ConnectFour


class _MCTSNode:
    """Single node in the MCTS search tree."""

    __slots__ = ("move", "parent", "children", "wins", "visits", "untried_moves")

    def __init__(self, move: int | None, parent: _MCTSNode | None, untried: list[int]):
        self.move = move
        self.parent = parent
        self.children: list[_MCTSNode] = []
        self.wins = 0.0
        self.visits = 0
        self.untried_moves = untried

    @property
    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def best_child(self, c: float = 1.41) -> _MCTSNode:
        """Select child with highest UCB1 score."""
        log_parent = math.log(self.visits)
        return max(
            self.children,
            key=lambda ch: (ch.wins / ch.visits) + c * math.sqrt(log_parent / ch.visits),
        )

    def best_move_child(self) -> _MCTSNode:
        """Select most-visited child (robust choice)."""
        return max(self.children, key=lambda ch: ch.visits)


@dataclass
class MCTSBot:
    """Monte Carlo Tree Search bot — lightweight but effective."""

    name: str = "mcts"
    simulations: int = 800

    def choose_move(self, game: ConnectFour, player: int, rng: random.Random) -> int:
        legal = game.legal_moves()
        if not legal:
            raise ValueError("No legal moves available")
        if len(legal) == 1:
            return legal[0]

        # Check for immediate wins/blocks before searching
        for col in legal:
            sim = game.clone()
            sim.drop(col)
            if sim.winner == player:
                return col
        for col in legal:
            sim = game.clone()
            sim.current_player = -player
            sim2 = sim.clone()
            sim2.current_player = -player
            sim2.drop(col)
            if sim2.winner == -player:
                return col

        root = _MCTSNode(move=None, parent=None, untried=legal[:])
        root_state = game.clone()

        for _ in range(self.simulations):
            node = root
            state = root_state.clone()

            # Selection — walk down the tree using UCB1
            while node.is_fully_expanded and node.children:
                node = node.best_child()
                state.drop(node.move)

            # Expansion — add one child for an untried move
            if node.untried_moves and state.winner is None:
                move = rng.choice(node.untried_moves)
                node.untried_moves.remove(move)
                state.drop(move)
                child = _MCTSNode(move=move, parent=node, untried=state.legal_moves())
                node.children.append(child)
                node = child

            # Simulation — random playout to terminal
            sim_state = state.clone()
            while sim_state.winner is None:
                moves = sim_state.legal_moves()
                if not moves:
                    break
                sim_state.drop(rng.choice(moves))

            # Backpropagation
            result = sim_state.winner
            if result is None:
                reward = 0.5
            elif result == 0:
                reward = 0.5
            elif result == player:
                reward = 1.0
            else:
                reward = 0.0

            while node is not None:
                node.visits += 1
                node.wins += reward
                node = node.parent

        return root.best_move_child().move
