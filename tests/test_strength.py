"""Strength-ordering smoke test with fixed seed for reproducibility.

Asserts the expected skill hierarchy: minimax > mcts > greedy > random.
Uses the tournament runner directly so this validates the full pipeline.
"""

from arena.router import build_default_router
from arena.tournament import TournamentRunner

# Fixed benchmark parameters — must match snapshots/baseline.md
BENCHMARK_SEED = 42
BENCHMARK_ROUNDS = 3
BENCHMARK_GAMES_PER_PAIR = 2
BENCHMARK_BOTS = ["minimax", "mcts", "greedy", "random"]


def test_strength_ordering() -> None:
    """Minimax > mcts > greedy > random over enough games with fixed seed."""
    router = build_default_router()
    runner = TournamentRunner(router=router, seed=BENCHMARK_SEED, k_factor=24.0)
    report = runner.run(
        bot_names=BENCHMARK_BOTS,
        rounds=BENCHMARK_ROUNDS,
        games_per_pair=BENCHMARK_GAMES_PER_PAIR,
    )

    ratings = dict(report.leaderboard())
    assert ratings["minimax"] > ratings["mcts"], (
        f"minimax ({ratings['minimax']:.1f}) should beat mcts ({ratings['mcts']:.1f})"
    )
    assert ratings["mcts"] > ratings["greedy"], (
        f"mcts ({ratings['mcts']:.1f}) should beat greedy ({ratings['greedy']:.1f})"
    )
    assert ratings["greedy"] > ratings["random"], (
        f"greedy ({ratings['greedy']:.1f}) should beat random ({ratings['random']:.1f})"
    )


def test_minimax_dominates_random() -> None:
    """Minimax should win nearly every game against random."""
    router = build_default_router()
    runner = TournamentRunner(router=router, seed=BENCHMARK_SEED, k_factor=24.0)
    report = runner.run(
        bot_names=["minimax", "random"],
        rounds=3,
        games_per_pair=2,
    )
    stats = report.stats()
    assert stats["minimax"]["wins"] >= 5, (
        f"minimax only won {stats['minimax']['wins']}/6 against random"
    )
    assert stats["random"]["wins"] == 0, (
        f"random should not beat minimax but won {stats['random']['wins']}"
    )
