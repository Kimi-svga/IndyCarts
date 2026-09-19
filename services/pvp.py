"""PvP-рейтинг по системе Эло."""

from dataclasses import dataclass


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
    """
    Считает изменение рейтинга после дуэли.

    Формула:
        expected = 1 / (1 + 10 ** ((opponent - player) / 400))
        delta = K × (1 - expected)
    """
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    delta = int(k * (1 - expected_winner))
    delta = max(1, delta)
    return EloResult(winner_delta=delta, loser_delta=-delta)


def get_rank_title(rating: int) -> str:
    """Возвращает титул по рейтингу."""
    if rating >= 2000:
        return "👑 Легенда"
    elif rating >= 1700:
        return "🏆 Чемпион"
    elif rating >= 1400:
        return "⭐ Элита"
    elif rating >= 1200:
        return "🔥 Про"
    elif rating >= 1000:
        return "🟢 Новичок"
    else:
        return "⚪ Стажёр"
