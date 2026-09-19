"""Слияние карт: 3 → 1."""

import random
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MERGE_RULES
from db.models import Card, UserCard
from services.drop import Drop


@dataclass
class MergeResult:
    """Результат слияния."""
    ok: bool
    result: Optional[str] = None
    card_name: Optional[str] = None
    reason: Optional[str] = None


async def merge_cards(
    session: AsyncSession,
    user_id: int,
    rarity: str,
) -> MergeResult:
    """
    Сливает 3 карты одной редкости.

    Шансы в MERGE_RULES.
    Legendary → Limited: 20%.
    """
    if rarity not in MERGE_RULES:
        return MergeResult(ok=False, reason="Эту редкость нельзя объединить")

    rule = MERGE_RULES[rarity]

    stmt = (
        select(UserCard)
        .join(Card, UserCard.card_id == Card.id)
        .where(UserCard.user_id == user_id, Card.rarity == rarity)
        .limit(3)
    )
    cards = (await session.execute(stmt)).scalars().all()

    if len(cards) < 3:
        return MergeResult(ok=False, reason=f"Нужно 3 карты {rarity}")

    for c in cards:
        await session.delete(c)

    if random.random() < rule["chance"]:
        new_card = await Drop.get_random_card(session, rule["result"])
        if new_card is not None:
            session.add(UserCard(
                user_id=user_id,
                card_id=new_card.id,
                acquired_price=new_card.current_price,
            ))
            await session.commit()
            return MergeResult(
                ok=True,
                result=rule["result"],
                card_name=new_card.name,
            )
        await session.commit()
        return MergeResult(ok=False, reason="Нет карт этой редкости")

    await session.commit()
    return MergeResult(ok=True, result="burn") 
