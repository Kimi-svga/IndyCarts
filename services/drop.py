import random
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from db.models import Card


def roll_rarity() -> str:
    rarities = list(DROP_CHANCES.keys())
    weights = list(DROP_CHANCES.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def roll_iw() -> bool:
    return random.randint(1, 100) <= IW_CHANCE


async def get_random_card_by_rarity(session: AsyncSession, rarity: str) -> Card | None:
    stmt = (
        select(Card)
        .where(Card.rarity == rarity, Card.is_active == True)
        .order_by(func.random())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def drop_card(session: AsyncSession) -> tuple[Card | None, bool]:
    rarity = roll_rarity()
    is_iw = roll_iw()
    card = await get_random_card_by_rarity(session, rarity)
    if not card:
        card = await get_random_card_by_rarity(session, "common")
    return card, is_iw
