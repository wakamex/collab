from __future__ import annotations

from typing import Callable, Dict, List

from .bot import Bot, GreedyBot, RandomBot
from .mcts_bot import MCTSBot
from .minimax_bot import MinimaxBot
from .hybrid_bot import HybridBot
from .negamax_bot import NegamaxBot


BotFactory = Callable[[], Bot]


class BotRouter:
    """Registry-based strategy router."""

    def __init__(self) -> None:
        self._registry: Dict[str, BotFactory] = {}

    def register(self, name: str, factory: BotFactory) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("Bot name must not be empty")
        self._registry[key] = factory

    def create(self, name: str) -> Bot:
        key = name.strip().lower()
        if key not in self._registry:
            available = ", ".join(self.names())
            raise KeyError(f"Unknown bot '{name}'. Available: {available}")
        return self._registry[key]()

    def names(self) -> List[str]:
        return sorted(self._registry)


def build_default_router() -> BotRouter:
    router = BotRouter()
    router.register("random", lambda: RandomBot(name="random"))
    router.register("greedy", lambda: GreedyBot(name="greedy"))
    router.register("minimax", lambda: MinimaxBot(name="minimax"))
    router.register("mcts", lambda: MCTSBot(name="mcts"))
    router.register("hybrid", lambda: HybridBot(name="hybrid"))
    router.register("negamax", lambda: NegamaxBot(name="negamax"))

    # Collaborative aliases so each partner has a baseline identity bot.
    router.register("dex", lambda: GreedyBot(name="dex"))
    router.register("clod", lambda: NegamaxBot(name="clod"))
    return router
