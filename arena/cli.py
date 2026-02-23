from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .router import build_default_router
from .tournament import MatchRecord, TournamentReport, TournamentRunner


DEFAULT_CONFIG = {
    "bots": ["dex", "clod", "random", "greedy", "minimax", "mcts", "negamax", "hybrid"],
    "rounds": 1,
    "games_per_pair": 2,
    "seed": 42,
    "k_factor": 24.0,
    "recent_games": 20,
}

PRESETS = {
    "baseline-6": {
        "bots": ["dex", "clod", "random", "greedy", "minimax", "mcts"],
        "rounds": 3,
        "games_per_pair": 2,
        "seed": 42,
        "k_factor": 24.0,
        "recent_games": 20,
    },
    "full-8": {
        "bots": ["dex", "clod", "random", "greedy", "minimax", "mcts", "negamax", "hybrid"],
        "rounds": 3,
        "games_per_pair": 2,
        "seed": 42,
        "k_factor": 24.0,
        "recent_games": 30,
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Arena tournament runner")
    parser.add_argument("--list-bots", action="store_true", help="List available bot names and exit")
    parser.add_argument("--list-presets", action="store_true", help="List benchmark presets and exit")
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default=None,
        help="Apply a named benchmark preset before command-line overrides",
    )
    parser.add_argument(
        "--bots",
        nargs="+",
        default=None,
        help="Bot names to include in tournament",
    )
    parser.add_argument("--rounds", type=int, default=None, help="Number of round-robin cycles")
    parser.add_argument("--games-per-pair", type=int, default=None, help="Games per bot pair per round")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--k-factor", type=float, default=None, help="ELO k-factor")
    parser.add_argument("--recent-games", type=int, default=None, help="Number of recent games to print in markdown")
    parser.add_argument("--markdown-out", type=Path, default=None, help="Write markdown report to this path")
    parser.add_argument("--json-out", type=Path, default=None, help="Write match records as JSON")
    return parser


def _resolve_config(args: argparse.Namespace) -> Dict[str, object]:
    config: Dict[str, object] = dict(DEFAULT_CONFIG)
    if args.preset is not None:
        config.update(PRESETS[args.preset])

    overrides = {
        "bots": args.bots,
        "rounds": args.rounds,
        "games_per_pair": args.games_per_pair,
        "seed": args.seed,
        "k_factor": args.k_factor,
        "recent_games": args.recent_games,
    }
    for key, value in overrides.items():
        if value is not None:
            config[key] = value
    return config


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
    if args.list_presets:
        for name in sorted(PRESETS):
            preset = PRESETS[name]
            bots = ",".join(preset["bots"])
            print(
                f"{name}: rounds={preset['rounds']} games_per_pair={preset['games_per_pair']} "
                f"seed={preset['seed']} bots={bots}"
            )
        return 0

    config = _resolve_config(args)

    rounds = int(config["rounds"])
    games_per_pair = int(config["games_per_pair"])
    seed = int(config["seed"])
    k_factor = float(config["k_factor"])
    recent_games = int(config["recent_games"])
    bots = list(config["bots"])

    if rounds < 1:
        parser.error("--rounds must be >= 1")
    if games_per_pair < 1:
        parser.error("--games-per-pair must be >= 1")

    runner = TournamentRunner(router=router, seed=seed, k_factor=k_factor)
    report = runner.run(bot_names=bots, rounds=rounds, games_per_pair=games_per_pair)

    print(_render_leaderboard(report))

    if args.markdown_out is not None:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(report.to_markdown(recent_games=recent_games) + "\n", encoding="utf-8")
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
