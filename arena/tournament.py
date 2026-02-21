from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .bot import Bot
from .elo import EloLadder
from .game import ConnectFour, PLAYER_ONE, PLAYER_TWO
from .router import BotRouter


@dataclass
class MatchRecord:
    game_id: int
    round_index: int
    player_one: str
    player_two: str
    winner: Optional[str]
    moves: int
    score_player_one: float
    rating_delta_player_one: float
    rating_delta_player_two: float


@dataclass
class TournamentReport:
    records: List[MatchRecord]
    ratings: Dict[str, float]

    def leaderboard(self) -> List[Tuple[str, float]]:
        return sorted(self.ratings.items(), key=lambda item: (-item[1], item[0]))

    def stats(self) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = {
            name: {"games": 0, "wins": 0, "losses": 0, "draws": 0}
            for name in self.ratings
        }
        for record in self.records:
            p1 = record.player_one
            p2 = record.player_two
            stats[p1]["games"] += 1
            stats[p2]["games"] += 1
            if record.winner is None:
                stats[p1]["draws"] += 1
                stats[p2]["draws"] += 1
            elif record.winner == p1:
                stats[p1]["wins"] += 1
                stats[p2]["losses"] += 1
            else:
                stats[p2]["wins"] += 1
                stats[p1]["losses"] += 1
        return stats

    def head_to_head(self) -> Dict[Tuple[str, str], Dict[str, int]]:
        out: Dict[Tuple[str, str], Dict[str, int]] = {}
        for record in self.records:
            a, b = sorted((record.player_one, record.player_two))
            if (a, b) not in out:
                out[(a, b)] = {a: 0, b: 0, "draws": 0}
            if record.winner is None:
                out[(a, b)]["draws"] += 1
            else:
                out[(a, b)][record.winner] += 1
        return out

    def to_markdown(self, recent_games: int = 20) -> str:
        stats = self.stats()
        lines: List[str] = []
        lines.append("# Arena Leaderboard")
        lines.append("")
        lines.append("| Rank | Bot | Rating | Games | W | L | D |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
        for rank, (name, rating) in enumerate(self.leaderboard(), start=1):
            bot_stats = stats.get(name, {"games": 0, "wins": 0, "losses": 0, "draws": 0})
            lines.append(
                f"| {rank} | {name} | {rating:.1f} | {bot_stats['games']} | "
                f"{bot_stats['wins']} | {bot_stats['losses']} | {bot_stats['draws']} |"
            )

        lines.append("")
        lines.append("## Head-to-Head")
        lines.append("")
        lines.append("| Bot A | Bot B | A Wins | B Wins | Draws |")
        lines.append("| --- | --- | ---: | ---: | ---: |")
        for (a, b), h2h in sorted(self.head_to_head().items()):
            lines.append(f"| {a} | {b} | {h2h[a]} | {h2h[b]} | {h2h['draws']} |")

        lines.append("")
        lines.append("## Recent Games")
        lines.append("")
        lines.append("| Game | Round | P1 | P2 | Winner | Moves | Delta P1 | Delta P2 |")
        lines.append("| ---: | ---: | --- | --- | --- | ---: | ---: | ---: |")

        for record in self.records[-recent_games:]:
            winner = record.winner if record.winner is not None else "draw"
            lines.append(
                f"| {record.game_id} | {record.round_index} | {record.player_one} | "
                f"{record.player_two} | {winner} | {record.moves} | "
                f"{record.rating_delta_player_one:+.2f} | {record.rating_delta_player_two:+.2f} |"
            )
        return "\n".join(lines)


class TournamentRunner:
    def __init__(self, router: BotRouter, seed: int = 42, k_factor: float = 24.0) -> None:
        self.router = router
        self.rng = random.Random(seed)
        self.ladder = EloLadder(k_factor=k_factor)

    def run(self, bot_names: Sequence[str], rounds: int = 1, games_per_pair: int = 2) -> TournamentReport:
        unique_names = self._normalize_names(bot_names)
        for name in unique_names:
            self.ladder.ensure(name)

        records: List[MatchRecord] = []
        game_id = 1
        for round_index in range(1, rounds + 1):
            for i in range(len(unique_names)):
                for j in range(i + 1, len(unique_names)):
                    a = unique_names[i]
                    b = unique_names[j]
                    for g in range(games_per_pair):
                        if g % 2 == 0:
                            p1, p2 = a, b
                        else:
                            p1, p2 = b, a
                        bot_one = self.router.create(p1)
                        bot_two = self.router.create(p2)
                        winner, moves = self._play_single_game(bot_one, bot_two, p1, p2)
                        score_p1 = self._score_for_player_one(winner, p1)
                        delta_p1, delta_p2 = self.ladder.record(p1, p2, score_p1)
                        records.append(
                            MatchRecord(
                                game_id=game_id,
                                round_index=round_index,
                                player_one=p1,
                                player_two=p2,
                                winner=winner,
                                moves=moves,
                                score_player_one=score_p1,
                                rating_delta_player_one=delta_p1,
                                rating_delta_player_two=delta_p2,
                            )
                        )
                        game_id += 1
        return TournamentReport(records=records, ratings=dict(self.ladder.ratings))

    def _normalize_names(self, bot_names: Sequence[str]) -> List[str]:
        names: List[str] = []
        seen = set()
        for raw in bot_names:
            key = raw.strip().lower()
            if not key or key in seen:
                continue
            self.router.create(key)  # validates existence
            names.append(key)
            seen.add(key)
        if len(names) < 2:
            raise ValueError("Need at least two distinct bot names")
        return names

    def _play_single_game(
        self, bot_one: Bot, bot_two: Bot, label_one: str, label_two: str
    ) -> Tuple[Optional[str], int]:
        game = ConnectFour()
        while not game.is_terminal():
            player = game.current_player
            active_bot = bot_one if player == PLAYER_ONE else bot_two
            try:
                selected = active_bot.choose_move(game.clone(), player, self.rng)
            except Exception:
                winner = label_two if player == PLAYER_ONE else label_one
                return winner, game.moves_played

            legal = game.legal_moves()
            if selected not in legal:
                winner = label_two if player == PLAYER_ONE else label_one
                return winner, game.moves_played

            game.drop(selected)

        if game.winner == PLAYER_ONE:
            return label_one, game.moves_played
        if game.winner == PLAYER_TWO:
            return label_two, game.moves_played
        return None, game.moves_played

    @staticmethod
    def _score_for_player_one(winner: Optional[str], player_one: str) -> float:
        if winner is None:
            return 0.5
        return 1.0 if winner == player_one else 0.0
