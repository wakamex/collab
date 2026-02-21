from arena.router import build_default_router
from arena.tournament import TournamentRunner


def test_tournament_generates_records_and_ratings() -> None:
    router = build_default_router()
    runner = TournamentRunner(router=router, seed=7, k_factor=24.0)

    report = runner.run(bot_names=["random", "greedy"], rounds=2, games_per_pair=2)

    assert len(report.records) == 4
    assert set(report.ratings) == {"random", "greedy"}

    stats = report.stats()
    assert stats["random"]["games"] == 4
    assert stats["greedy"]["games"] == 4

    markdown = report.to_markdown(recent_games=3)
    assert "Head-to-Head" in markdown
    assert "| random | greedy |" in markdown or "| greedy | random |" in markdown


def test_router_has_advanced_bots_registered() -> None:
    router = build_default_router()
    names = router.names()
    assert "minimax" in names
    assert "mcts" in names
