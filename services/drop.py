"""Логика дропа карт."""

import random
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from db.models import Card


class Drop:
    """Дроп карт."""

    @staticmethod
    def roll_rarity() -> str:
        """Выбирает редкость по шансам."""
        rarities = list(DROP_CHANCES.keys())
        weights = list(DROP_CHANCES.values())
        return random.choices(rarities, weights=weights, k=1)[0]

    @staticmethod
    def roll_iw() -> bool:
        """Проверяет, выпал ли INDY Winner."""
        return random.randint(1, 100) <= IW_CHANCE

    @staticmethod
    async def get_random_card(session: AsyncSession, rarity: str) -> Card | None:
        """Берёт случайную карту с учётом лимита."""
        stmt = (
            select(Card)
            .where(
                Card.rarity == rarity,
                Card.is_active == True,
                (Card.max_supply == None) | (Card.issued < Card.max_supply)
            )
            .order_by(func.random() * Card.drop_weight)
            .limit(1)
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_any_card(session: AsyncSession) -> Card | None:
        """Фолбэк: любая активная карта."""
        stmt = (
            select(Card)
            .where(
                Card.is_active == True,
                (Card.max_supply == None) | (Card.issued < Card.max_supply)
            )
            .order_by(func.random())
            .limit(1)
        )
        return (await session.execute(stmt)).scalar_one_or_none()


async def drop_card(session: AsyncSession) -> tuple[Card | None, bool]:
    """Один дроп: (карта, is_iw)."""
    rarity = Drop.roll_rarity()
    is_iw = Drop.roll_iw()
    card = await Drop.get_random_card(session, rarity)
    if not card:
        card = await Drop.get_any_card(session)
    return card, is_iw


def roll_rarity():
    return Drop.roll_rarity()


def roll_iw():
    return Drop.roll_iw()


async def get_random_card(session, rarity):
    return await Drop.get_random_card(session, rarity)


async def get_any_card(session):
    return await Drop.get_any_card(session) 
