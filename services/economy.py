"""Экономические формулы и индекс цен."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import CEILING_MULTIPLIER, FLOOR_MULTIPLIER, IW_MULTIPLIER
from db.models import Card, PriceHistory


class Economy:
    """Формулы цены. Все методы — @staticmethod."""

    @staticmethod
    def calculate_price(
        base_price: int,
        demand: int = 0,
        supply: int = 0,
        event: float = 1.0,
        is_iw: bool = False,
    ) -> int:
        """
        Считает цену карты.

        Формула: base × (demand/supply) × event × iw
        Ограничения: floor = base × 0.3, ceiling = base × 5.0
        """
        iw_mult = IW_MULTIPLIER if is_iw else 1

        if supply > 0 and demand > 0:
            ratio = demand / supply
        elif demand > 0:
            ratio = 2.0
        else:
            ratio = 1.0

        ratio = max(0.3, min(ratio, 3.0))
        price = base_price * ratio * event * iw_mult

        floor = int(base_price * FLOOR_MULTIPLIER)
        ceiling = int(base_price * CEILING_MULTIPLIER)
        return int(max(floor, min(price, ceiling)))

    @staticmethod
    def decay_price(current: int, base: int, rate: float = 0.05) -> int:
        """Плавно возвращает цену к базовой (5% в час)."""
        diff = current - base
        if abs(diff) < base * 0.01:
            return base
        return int(current - diff * rate)


async def get_price_change(
    session: AsyncSession,
    card_id: int,
    hours: int = 24,
) -> float:
    """
    Возвращает % изменения цены за N часов.

    Если данных нет — 0.0.
    """
    now = datetime.utcnow()
    past = now - timedelta(hours=hours)

    card = (await session.execute(
        select(Card).where(Card.id == card_id)
    )).scalar_one_or_none()
    if card is None:
        return 0.0

    stmt = (
        select(PriceHistory)
        .where(
            PriceHistory.card_id == card_id,
            PriceHistory.recorded_at <= past,
        )
        .order_by(PriceHistory.recorded_at.desc())
        .limit(1)
    )
    old = (await session.execute(stmt)).scalar_one_or_none()
    if old is None or old.price == 0:
        return 0.0

    return ((card.current_price - old.price) / old.price) * 100


def format_change(change: float) -> str:
    """Форматирует изменение цены с эмодзи."""
    if change > 5:
        return f"📈 <b>+{change:.1f}%</b>"
    elif change > 0:
        return f"↗️ +{change:.1f}%"
    elif change < -5:
        return f"📉 <b>{change:.1f}%</b>"
    elif change < 0:
        return f"↘️ {change:.1f}%"
    return "➡️ 0%" 
