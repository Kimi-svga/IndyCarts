"""Дроп карт с учётом редкости, веса и лимита тиража."""

import random
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from core.logger import setup_logger
from db.models import Card

logger = setup_logger()


class Drop:
    """Логика дропа. Все методы — @staticmethod."""

    @staticmethod
    def roll_rarity() -> str:
        """Выбирает редкость по весам DROP_CHANCES."""
        rarities = list(DROP_CHANCES.keys())
        weights = list(DROP_CHANCES.values())
        return random.choices(rarities, weights=weights, k=1)[0]

    @staticmethod
    def roll_iw() -> bool:
        """Проверяет, выпал ли INDY Winner."""
        return random.randint(1, 100) <= IW_CHANCE

    @staticmethod
    async def get_random_card(
        session: AsyncSession,
        rarity: str,
    ) -> Optional[Card]:
        """
        Берёт случайную карту редкости с учётом:
        - is_active,
        - лимита тиража (issued < max_supply),
        - веса drop_weight.

        with_for_update — атомарная блокировка от race condition.
        """
        stmt = (
            select(Card)
            .where(
                Card.rarity == rarity,
                Card.is_active == True,  # noqa: E712
                (Card.max_supply == None) | (Card.issued < Card.max_supply),  # noqa: E711
            )
            .order_by(func.random() * Card.drop_weight)
            .limit(1)
            .with_for_update()
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_any_card(session: AsyncSession) -> Optional[Card]:
        """Фолбэк: любая активная карта с учётом лимита."""
        stmt = (
            select(Card)
            .where(
                Card.is_active == True,  # noqa: E712
                (Card.max_supply == None) | (Card.issued < Card.max_supply),  # noqa: E711
            )
            .order_by(func.random())
            .limit(1)
            .with_for_update()
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def drop_card(session: AsyncSession) -> Tuple[Optional[Card], bool]:
        """Один дроп: (карта, is_iw)."""
        rarity = Drop.roll_rarity()
        is_iw = Drop.roll_iw()
        card = await Drop.get_random_card(session, rarity)
        if card is None:
            logger.warning(f"Нет карт редкости {rarity}, фолбэк")
            card = await Drop.get_any_card(session)
        return card, is_iw 
