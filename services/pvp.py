
"""PvP: Эло, титулы, сезоны."""

from dataclasses import dataclass
from datetime import datetime

from core.constants import PVP_TITLES


START_RATING = 1000
K_FACTOR = 32


@dataclass
class EloResult:
    """Результат пересчёта Эло."""
    winner_delta: int
    loser_delta: int


def calculate_elo(
    winner_rating: int,
    loser_rating: int,
    k: int = K_FACTOR,
) -> EloResult:
    """Считает изменение рейтинга после дуэли."""
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    delta = int(k * (1 - expected_winner))
    delta = max(1, delta)
    return EloResult(winner_delta=delta, loser_delta=-delta)


def get_rank_title(rating: int) -> str:
    """Возвращает титул по рейтингу."""
    for threshold, title in PVP_TITLES:
        if rating >= threshold:
            return title
    return "⚪ Стажёр"


def calculate_pvp_money_prize(
    stake_challenger: int,
    stake_opponent: int,
    commission: float = 0.10,
) -> int:
    """
    Победитель забирает всё, игра забирает комиссию.
    """
    total = stake_challenger + stake_opponent
    prize = int(total * (1 - commission))
    return prize


def days_until_season_end(ends_at: datetime) -> int:
    """Сколько дней до конца сезона."""
    diff = ends_at - datetime.utcnow()
    return max(0, diff.days) 
