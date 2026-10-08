"""Дроп карт с учётом редкости, веса, лимита тиража и кланового бонуса."""

import random
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from core.logger import setup_logger
from db.models import Card

logger = setup_logger()

# Редкости, на которые влияет клановый бонус дропа
BONUS_RARITIES = ("legendary", "limited", "season")


class Drop:
    """Логика дропа. Все методы — @staticmethod."""

    @staticmethod
    def roll_rarity(drop_bonus: float = 0.0) -> str:
        """
        Выбирает редкость по весам DROP_CHANCES.

        drop_bonus (0.0–0.5) — клановый бонус дропа.
        Повышает шанс редких редкостей (legendary/limited/season)
        за счёт базовых (basic/rare).

        Пример: drop_bonus=0.2 → +20% к редким.
        """
        weights = dict(DROP_CHANCES)

        if drop_bonus > 0:
            # Сдвигаем 30% от базовых редкостей в сторону редких
            shift_pool = 0.0
            for r in ("basic", "rare", "epic"):
                take = weights[r] * drop_bonus * 0.3
                weights[r] = max(0.0, weights[r] - take)
                shift_pool += take

            # Распределяем shift_pool между legendary/limited/season
            if weights["legendary"] + weights["limited"] + weights["season"] > 0:
                total_rare = weights["legendary"] + weights["limited"] + weights["season"]
                for r in ("legendary", "limited", "season"):
                    weights[r] += shift_pool * (weights[r] / total_rare)

        rarities = list(weights.keys())
        chances = list(weights.values())
        return random.choices(rarities, weights=chances, k=1)[0]

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
                Card.in_drop == True,  # noqa: E712
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
                Card.in_drop == True,  # noqa: E712
                (Card.max_supply == None) | (Card.issued < Card.max_supply),  # noqa: E711
            )
            .order_by(func.random())
            .limit(1)
            .with_for_update()
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def drop_card(session: AsyncSession) -> Tuple[Optional[Card], bool]:
        """Один дроп БЕЗ кланового бонуса (обратная совместимость)."""
        return await Drop.drop_card_with_bonus(session, 0.0)

    @staticmethod
    async def drop_card_with_bonus(
        session: AsyncSession,
        drop_bonus: float = 0.0,
    ) -> Tuple[Optional[Card], bool]:
        """
        Один дроп с клановым бонусом.

        drop_bonus: 0.0–0.5 (см. CLAN_LEVELS).
        Возвращает (карта, is_iw).
        """
        rarity = Drop.roll_rarity(drop_bonus)
        is_iw = Drop.roll_iw()

        card = await Drop.get_random_card(session, rarity)
        if card is None:
            logger.warning(f"Нет карт редкости {rarity}, фолбэк")
            card = await Drop.get_any_card(session)

        return card, is_iw 
