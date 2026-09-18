"""Формулы цены. Все методы — статические."""

from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import IW_MULTIPLIER, FLOOR_MULTIPLIER, CEILING_MULTIPLIER
from db.models import Card, PriceHistory


class Economy:
    """Экономика Indy Carts."""

    @staticmethod
    def calculate_price(
        base_price: int,
        demand: int = 0,
        supply: int = 0,
        event: float = 1.0,
        is_iw: bool = False,
    ) -> int:
        """Считает цену с учётом спроса, предложения и событий."""
        iw = IW_MULTIPLIER if is_iw else 1
        ratio = (demand / supply) if supply > 0 and demand > 0 else (2.0 if demand > 0 else 1.0)
        ratio = max(0.3, min(ratio, 3.0))
        price = base_price * ratio * event * iw
        floor = int(base_price * FLOOR_MULTIPLIER)
        ceiling = int(base_price * CEILING_MULTIPLIER)
        return int(max(floor, min(price, ceiling)))

    @staticmethod
    def decay_price(current: int, base: int, rate: float = 0.05) -> int:
        """Плавно возвращает цену к базовой."""
        diff = current - base
        if abs(diff) < base * 0.01:
            return base
        return int(current - diff * rate)


async def get_price_change(session: AsyncSession, card_id: int, hours: int = 24) -> float:
    """Возвращает % изменения цены за N часов."""
    now = datetime.utcnow()
    past = now - timedelta(hours=hours)

    card = (await session.execute(select(Card).where(Card.id == card_id))).scalar_one_or_none()
    if not card:
        return 0.0

    stmt = (
        select(PriceHistory)
        .where(PriceHistory.card_id == card_id, PriceHistory.recorded_at <= past)
        .order_by(PriceHistory.recorded_at.desc())
        .limit(1)
    )
    old = (await session.execute(stmt)).scalar_one_or_none()

    if not old or old.price == 0:
        return 0.0

    return ((card.current_price - old.price) / old.price) * 100


def format_change(change: float) -> str:
    """Форматирует изменение в строку с эмодзи."""
    if change > 5:
        return f"📈 <b>+{change:.1f}%</b>"
    elif change > 0:
        return f"↗️ +{change:.1f}%"
    elif change < -5:
        return f"📉 <b>{change:.1f}%</b>"
    elif change < 0:
        return f"↘️ {change:.1f}%"
    else:
        return "➡️ 0%"


# Совместимость со старым кодом
def calculate_price(base_price, demand=0, supply=0, event=1.0, is_iw=False):
    return Economy.calculate_price(base_price, demand, supply, event, is_iw)


def decay_price(current, base, rate=0.05):
    return Economy.decay_price(current, base, rate) 
