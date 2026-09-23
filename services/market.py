"""Биржа: расчёт цены, движение, событие."""

import random
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import (
    CEILING_MULTIPLIER, FLOOR_MULTIPLIER,
    RARITY_BASIC, RARITY_EPIC, RARITY_LEGENDARY,
    RARITY_LIMITED, RARITY_MYTHIC, RARITY_RARE, RARITY_SEASON,
)
from core.logger import setup_logger
from db.models import Card, Transaction, UserCard

logger = setup_logger()


RARITY_WEIGHT = {
    RARITY_BASIC: 1.0,
    RARITY_RARE: 1.5,
    RARITY_EPIC: 2.5,
    RARITY_MYTHIC: 4.0,
    RARITY_LEGENDARY: 7.0,
    RARITY_LIMITED: 10.0,
    RARITY_SEASON: 15.0,
}

TEAM_WEIGHT = {
    "Chip Ganassi Racing": 1.3,
    "Team Penske": 1.3,
    "Andretti Global": 1.2,
    "Arrow McLaren": 1.2,
    "A.J. Foyt Racing": 1.0,
    "Rahal Letterman Lanigan": 1.0,
    "Ed Carpenter Racing": 0.9,
    "Juncos Hollinger Racing": 0.8,
}


def year_weight(year: int | None) -> float:
    if year is None:
        return 1.0
    current_year = datetime.utcnow().year
    age = current_year - year
    if age <= 1:
        return 1.0
    elif age <= 3:
        return 1.1
    elif age <= 5:
        return 1.2
    elif age <= 10:
        return 1.3
    else:
        return 1.5


class Market:
    """Биржа Indy Carts."""

    @staticmethod
    def calculate_value(card: Card) -> float:
        """Ценность карты: rarity × team × year."""
        rarity = RARITY_WEIGHT.get(card.rarity, 1.0)
        team = TEAM_WEIGHT.get(card.team or "", 1.0)
        year = year_weight(card.year)
        return rarity * team * year

    @staticmethod
    def calculate_random_price(card: Card) -> int:
        """Цена с рандомом: base × value × random(0.7, 1.3)."""
        value = Market.calculate_value(card)
        random_factor = random.uniform(0.7, 1.3)

        price = int(card.base_price * value * random_factor)

        floor = int(card.base_price * FLOOR_MULTIPLIER)
        ceiling = int(card.base_price * CEILING_MULTIPLIER)

        return max(floor, min(price, ceiling))

    @staticmethod
    async def calculate_demand(session: AsyncSession, card_id: int, hours: int = 24) -> int:
        """Спрос: сколько покупок за N часов."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(func.count(Transaction.id))
            .where(
                Transaction.card_id == card_id,
                Transaction.type == "buy",
                Transaction.created_at >= cutoff,
            )
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def calculate_supply(session: AsyncSession, card_id: int) -> int:
        """Предложение: сколько карт в обороте."""
        stmt = select(func.count(UserCard.id)).where(UserCard.card_id == card_id)
        result = await session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def recalculate_price(session: AsyncSession, card: Card) -> int:
        """Пересчёт цены: base × value × (demand/supply) × random."""
        demand = await Market.calculate_demand(session, card.id)
        supply = await Market.calculate_supply(session, card.id)

        if supply == 0:
            ratio = 1.5
        else:
            ratio = demand / supply if demand > 0 else 0.8

        ratio = max(0.5, min(ratio, 3.0))
        value = Market.calculate_value(card)
        random_factor = random.uniform(0.9, 1.1)

        new_price = int(card.base_price * value * ratio * random_factor)

        floor = int(card.base_price * FLOOR_MULTIPLIER)
        ceiling = int(card.base_price * CEILING_MULTIPLIER)
        return max(floor, min(new_price, ceiling))

    @staticmethod
    async def simulate_market_movement(session: AsyncSession) -> int:
        """Искусственное движение цен ±3–8% каждые 10 минут."""
        cards = (await session.execute(
            select(Card).where(Card.is_active == True)
        )).scalars().all()

        changed = 0
        for card in cards:
            change_percent = random.uniform(-0.08, 0.08)

            value = Market.calculate_value(card)
            if value > 5:
                change_percent *= 0.5

            new_price = int(card.current_price * (1 + change_percent))

            floor = int(card.base_price * FLOOR_MULTIPLIER)
            ceiling = int(card.base_price * CEILING_MULTIPLIER)
            new_price = max(floor, min(new_price, ceiling))

            if new_price != card.current_price:
                card.current_price = new_price
                changed += 1

        await session.commit()
        logger.info(f"📊 Биржа: изменено {changed} карт")
        return changed

    @staticmethod
    async def apply_event(session: AsyncSession, card_id: int, modifier: float) -> int:
        """Событие по одной карте."""
        card = (await session.execute(
            select(Card).where(Card.id == card_id)
        )).scalar_one_or_none()

        if card is None:
            return 0

        new_price = int(card.current_price * modifier)
        floor = int(card.base_price * FLOOR_MULTIPLIER)
        ceiling = int(card.base_price * CEILING_MULTIPLIER)
        new_price = max(floor, min(new_price, ceiling))

        card.current_price = new_price
        await session.commit()

        logger.info(f"📈 Событие: {card.name} → {new_price}")
        return new_price
