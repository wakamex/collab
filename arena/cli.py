from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .router import build_default_router
from .tournament import MatchRecord, TournamentReport, TournamentRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arena tournament runner")
    parser.add_argument("--list-bots", action="store_true", help="List available bot names and exit")
    parser.add_argument(
        "--bots",
        nargs="+",
        default=["dex", "clod", "random", "greedy", "minimax", "mcts"],
        help="Bot names to include in tournament",
    )
    parser.add_argument("--rounds", type=int, default=1, help="Number of round-robin cycles")
    parser.add_argument("--games-per-pair", type=int, default=2, help="Games per bot pair per round")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--k-factor", type=float, default=24.0, help="ELO k-factor")
    parser.add_argument("--recent-games", type=int, default=20, help="Number of recent games to print in markdown")
    parser.add_argument("--markdown-out", type=Path, default=None, help="Write markdown report to this path")
    parser.add_argument("--json-out", type=Path, default=None, help="Write match records as JSON")
    return parser


def _render_leaderboard(report: TournamentReport) -> str:
    stats = report.stats()
    rows: List[str] = []
    rows.append("Rank  Bot       Rating  G   W   L   D")
    rows.append("----  --------  ------  --  --  --  --")
    for rank, (name, rating) in enumerate(report.leaderboard(), start=1):
        s = stats[name]
        rows.append(
            f"{rank:>4}  {name:<8}  {rating:>6.1f}  {s['games']:>2}  {s['wins']:>2}  {s['losses']:>2}  {s['draws']:>2}"
        )
    return "\n".join(rows)


def _records_to_json(records: List[MatchRecord]) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for record in records:
        out.append(
            {
                "game_id": record.game_id,
                "round_index": record.round_index,
                "player_one": record.player_one,
                "player_two": record.player_two,
                "winner": record.winner,
                "moves": record.moves,
                "score_player_one": record.score_player_one,
                "rating_delta_player_one": record.rating_delta_player_one,
                "rating_delta_player_two": record.rating_delta_player_two,
            }
        )
    return out


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    router = build_default_router()
    if args.list_bots:
        print("\n".join(router.names()))
        return 0

    if args.rounds < 1:
        parser.error("--rounds must be >= 1")
    if args.games_per_pair < 1:
        parser.error("--games-per-pair must be >= 1")

    runner = TournamentRunner(router=router, seed=args.seed, k_factor=args.k_factor)
    report = runner.run(bot_names=args.bots, rounds=args.rounds, games_per_pair=args.games_per_pair)

    print(_render_leaderboard(report))

    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(report.to_markdown(recent_games=args.recent_games) + "\n", encoding="utf-8")
        print(f"\nWrote markdown report: {args.markdown_out}")

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ratings": dict(report.leaderboard()),
            "records": _records_to_json(report.records),
        }
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON records: {args.json_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
