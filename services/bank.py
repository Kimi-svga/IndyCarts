"""Формулы банка 2.0: лимиты, ставки, сроки, ранги."""

from datetime import datetime, timedelta

from core.config import settings
from core.constants import LOAN_RATES, LOAN_TERMS, TRUST_DELTA, TRUST_RANKS
from db.models import User


def calculate_max_loan(user: User) -> int:
    """Максимальный кредит зависит от trust_score."""
    base = settings.BANK_MAX_LOAN
    trust = max(0, user.trust_score)

    if trust >= 300:
        multiplier = 2.0
    elif trust >= 200:
        multiplier = 1.8
    elif trust >= 100:
        multiplier = 1.6
    elif trust >= 50:
        multiplier = 1.4
    elif trust >= 20:
        multiplier = 1.2
    else:
        multiplier = 1.0

    return min(int(base * multiplier), settings.BANK_ABS_MAX_LOAN)


def get_loan_rate(amount: int) -> float:
    """Ставка зависит от суммы кредита."""
    for threshold, rate in LOAN_RATES:
        if amount <= threshold:
            return rate
    return LOAN_RATES[-1][1]


def get_loan_term(amount: int) -> int:
    """Срок зависит от суммы (дни)."""
    for threshold, term in LOAN_TERMS:
        if amount <= threshold:
            return term
    return LOAN_TERMS[-1][1]


def get_trust_rank(trust_score: int) -> str:
    """Возвращает титул по trust_score."""
    title = TRUST_RANKS[0][1]
    for threshold, name in TRUST_RANKS:
        if trust_score >= threshold:
            title = name
    return title


def calculate_total_due(amount: int) -> int:
    """Сумма к возврату."""
    rate = get_loan_rate(amount)
    return int(amount * (1 + rate))


def is_early_repay(loan) -> bool:
    """Погашение за 7+ дней до срока."""
    days_left = (loan.due_at - datetime.utcnow()).days
    return days_left >= 7


def early_repay_discount(amount: int) -> int:
    """Скидка при досрочном погашении."""
    return int(amount * settings.BANK_EARLY_DISCOUNT)


def apply_trust(user: User, action: str) -> int:
    """Меняет trust_score по событию. Возвращает дельту."""
    delta = TRUST_DELTA.get(action, 0)
    user.trust_score += delta
    return delta


def can_refinance(user: User) -> tuple[bool, str]:
    """Можно ли рефинансировать."""
    if user.last_refinance_at is None:
        return True, ""

    cooldown = timedelta(days=settings.BANK_REFINANCE_COOLDOWN_DAYS)
    if datetime.utcnow() - user.last_refinance_at < cooldown:
        left = cooldown - (datetime.utcnow() - user.last_refinance_at)
        hours = int(left.total_seconds() // 3600)
        return False, f"Рефинанс доступен через {hours}ч"

    return True, "" 
