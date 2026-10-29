"""Дроп карт с учётом редкости, веса, лимита тиража и кланового бонуса."""

import random
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from core.logger import setup_logger
from db.models import Card

logger = setup_logger()

BONUS_RARITIES = ("legendary", "limited", "season")


class Drop:
    @staticmethod
    def roll_rarity(drop_bonus: float = 0.0) -> str:
        weights = dict(DROP_CHANCES)
        if drop_bonus > 0:
            shift_pool = 0.0
            for r in ("basic", "rare", "epic"):
                take = weights[r] * drop_bonus * 0.3
                weights[r] = max(0.0, weights[r] - take)
                shift_pool += take
            if weights["legendary"] + weights["limited"] + weights["season"] > 0:
                total_rare = weights["legendary"] + weights["limited"] + weights["season"]
                for r in ("legendary", "limited", "season"):
                    weights[r] += shift_pool * (weights[r] / total_rare)
        rarities = list(weights.keys())
        chances = list(weights.values())
        return random.choices(rarities, weights=chances, k=1)[0]

    @staticmethod
    def roll_iw() -> bool:
        return random.randint(1, 100) <= IW_CHANCE

    @staticmethod
    def is_halloween() -> bool:
        today = date.today()
        if today.month == 10 and today.day in (29, 30, 31):
            return True
        if today.month == 11 and today.day in (1, 2):
            return True
        return False

    @staticmethod
    def is_night() -> bool:
        # МСК = UTC+3
        now = datetime.utcnow() + timedelta(hours=3)
        return 0 <= now.hour < 6

    @staticmethod
    async def get_random_card(session: AsyncSession, rarity: str) -> Optional[Card]:
        stmt = (
            select(Card)
            .where(
                Card.rarity == rarity,
                Card.is_active == True,
                Card.in_drop == True,
                (Card.max_supply == None) | (Card.issued < Card.max_supply),
            )
            .order_by(func.pow(func.random(), 1.0 / Card.drop_weight).desc())
            .limit(1)
            .with_for_update()
        )
        card = (await session.execute(stmt)).scalar_one_or_none()
        if card and card.max_supply is not None:
            card.issued += 1
            await session.flush()
        return card

    @staticmethod
    async def get_any_card(session: AsyncSession) -> Optional[Card]:
        stmt = (
            select(Card)
            .where(
                Card.is_active == True,
                Card.in_drop == True,
                (Card.max_supply == None) | (Card.issued < Card.max_supply),
            )
            .order_by(func.random())
            .limit(1)
            .with_for_update()
        )
        card = (await session.execute(stmt)).scalar_one_or_none()
        if card and card.max_supply is not None:
            card.issued += 1
            await session.flush()
        return card

    @staticmethod
    async def drop_card_with_bonus(
        session: AsyncSession, drop_bonus: float = 0.0
    ) -> Tuple[Optional[Card], bool, bool]:
        rarity = Drop.roll_rarity(drop_bonus)
        
        # Ночной бафф
        if Drop.is_night() and random.random() < 0.5:
            rarity = "legendary"

        is_iw = Drop.roll_iw()
        card = await Drop.get_random_card(session, rarity)
        if card is None:
            card = await Drop.get_any_card(session)

        is_cursed = False
        if Drop.is_halloween() and random.random() < 0.15:
            is_cursed = True
            logger.info(f"👻 Выпала проклятая карта: {card.name if card else 'None'}")

        return card, is_iw, is_cursed
