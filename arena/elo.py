from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_ratings(rating_a: float, rating_b: float, score_a: float, k_factor: float) -> Tuple[float, float]:
    expected_a = expected_score(rating_a, rating_b)
    expected_b = 1.0 - expected_a
    new_a = rating_a + k_factor * (score_a - expected_a)
    new_b = rating_b + k_factor * ((1.0 - score_a) - expected_b)
    return new_a, new_b


@dataclass
class EloLadder:
    default_rating: float = 1200.0
    k_factor: float = 24.0
    ratings: Dict[str, float] = field(default_factory=dict)

    def ensure(self, name: str) -> None:
        if name not in self.ratings:
            self.ratings[name] = self.default_rating

    def get(self, name: str) -> float:
        self.ensure(name)
        return self.ratings[name]

    def record(self, player_a: str, player_b: str, score_a: float) -> Tuple[float, float]:
        old_a = self.get(player_a)
        old_b = self.get(player_b)
        new_a, new_b = update_ratings(old_a, old_b, score_a, self.k_factor)
        self.ratings[player_a] = new_a
        self.ratings[player_b] = new_b
        return new_a - old_a, new_b - old_b

    def leaderboard(self) -> List[Tuple[str, float]]:
        return sorted(self.ratings.items(), key=lambda item: (-item[1], item[0]))
