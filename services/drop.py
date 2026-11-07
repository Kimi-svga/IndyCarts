"""Дроп карт с учётом редкости, веса, лимита тиража и кланового бонуса."""

import random
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import DROP_CHANCES, IW_CHANCE
from core.logger import setup_logger
from db.models import Card

logger = setup_logger()

BONUS_RARITIES = ("legendary", "limited", "season")

# Сколько раз пробуем перероллить редкость, если в пуле нет карт
RARITY_REROLL_ATTEMPTS = 3


class Drop:
    @staticmethod
    def roll_rarity(drop_bonus: float = 0.0, night_bonus: bool = False) -> str:
        weights = dict(DROP_CHANCES)

        # Мягкий ночной бафф: legendary-вес ×1.5, а не "50% принудительно"
        if night_bonus:
            weights["legendary"] = weights.get("legendary", 0) * 1.5

        # Клановый бонус: перекладываем часть веса basic/rare/epic в редкие
        if drop_bonus > 0:
            shift_pool = 0.0
            for r in ("basic", "rare", "epic"):
                take = weights[r] * min(drop_bonus, 0.5) * 0.3
                weights[r] = max(0.0, weights[r] - take)
                shift_pool += take
            total_rare = sum(weights[r] for r in ("legendary", "limited", "season"))
            if total_rare > 0 and shift_pool > 0:
                for r in ("legendary", "limited", "season"):
                    weights[r] += shift_pool * (weights[r] / total_rare)

        # Убираем нулевые веса, чтобы random.choices не падал
        items = [(r, w) for r, w in weights.items() if w > 0]
        if not items:
            return "basic"
        rarities, chances = zip(*items)
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
        now = datetime.now(timezone.utc) + timedelta(hours=3)
        return 0 <= now.hour < 6

    @staticmethod
    async def get_random_card(session: AsyncSession, rarity: str) -> Optional[Card]:
        """Честная взвешенная выборка внутри редкости.

        drop_weight — это относительный вес: 100 = стандарт,
        50 = вдвое реже, 200 = вдвое чаще.
        """
        stmt = (
            select(Card.id, Card.drop_weight)
            .where(
                Card.rarity == rarity,
                Card.is_active == True,
                Card.in_drop == True,
                (Card.max_supply == None) | (Card.issued < Card.max_supply),
            )
            .with_for_update()
        )
        rows = (await session.execute(stmt)).all()
        if not rows:
            return None

        ids = [r.id for r in rows]
        weights = [max(float(r.drop_weight or 0), 0.0001) for r in rows]
        chosen_id = random.choices(ids, weights=weights, k=1)[0]

        card = await session.get(Card, chosen_id, with_for_update=True)
        if card and card.max_supply is not None:
            card.issued += 1
            await session.flush()
        return card

    @staticmethod
    async def drop_card_with_bonus(
        session: AsyncSession, drop_bonus: float = 0.0
    ) -> Tuple[Optional[Card], bool, bool]:
        night = Drop.is_night()

        # Пробуем до RARITY_REROLL_ATTEMPTS раз: если в выпавшей редкости
        # нет доступных карт — переролливаем редкость, а не падаем
        # в равномерный рандом по всем картам.
        card = None
        for _ in range(RARITY_REROLL_ATTEMPTS):
            rarity = Drop.roll_rarity(drop_bonus, night_bonus=night)
            card = await Drop.get_random_card(session, rarity)
            if card is not None:
                break

        if card is None:
            logger.warning("Дроп: не удалось найти карту после рероллов")
            return None, False, False

        is_iw = Drop.roll_iw()

        is_cursed = False
        if Drop.is_halloween() and random.random() < 0.15:
            is_cursed = True
            logger.info(f"👻 Выпала проклятая карта: {card.name}")

        return card, is_iw, is_cursed
