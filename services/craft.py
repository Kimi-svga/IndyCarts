"""Логика крафта (создания особых карт)."""

import json
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Card, CraftRecipe, UserCard


@dataclass
class CraftResult:
    ok: bool
    result: Optional[str] = None
    card_name: Optional[str] = None
    reason: Optional[str] = None


async def get_available_recipes(session: AsyncSession) -> list[CraftRecipe]:
    return (await session.execute(
        select(CraftRecipe).where(CraftRecipe.is_active == True)
    )).scalars().all()


async def craft_card(
    session: AsyncSession,
    user_id: int,
    recipe_id: int,
) -> CraftResult:
    
    recipe = await session.get(CraftRecipe, recipe_id)
    if recipe is None or not recipe.is_active:
        return CraftResult(ok=False, reason="Рецепт не найден")

    try:
        ingredients = json.loads(recipe.ingredients)
    except Exception:
        return CraftResult(ok=False, reason="Ошибка в данных рецепта")

    cards_to_delete = []
    
    # Проверяем, есть ли у игрока нужные карты
    for card_id in ingredients:
        user_card = (await session.execute(
            select(UserCard).where(
                UserCard.user_id == user_id,
                UserCard.card_id == card_id,
                UserCard.is_locked == False
            ).limit(1)
        )).scalar_one_or_none()

        if user_card is None:
            card_info = await session.get(Card, card_id)
            card_name = card_info.name if card_info else f"#{card_id}"
            return CraftResult(
                ok=False, 
                reason=f"Не хватает карты: {card_name}"
            )
        
        cards_to_delete.append(user_card)

    # Удаляем сданные карты
    for uc in cards_to_delete:
        await session.delete(uc)

    # Получаем карту-результат
    result_card = await session.get(Card, recipe.result_card_id)
    if result_card is None:
        return CraftResult(ok=False, reason="Карта-результат не найдена")

    # Проверка тиража
    if result_card.max_supply is not None and result_card.issued >= result_card.max_supply:
        return CraftResult(ok=False, reason="Тираж награды исчерпан")

    if result_card.max_supply is not None:
        result_card.issued += 1

    # Выдаем карту
    session.add(UserCard(
        user_id=user_id,
        card_id=result_card.id,
        acquired_price=0,
        serial_number=result_card.issued if result_card.max_supply else None
    ))

    await session.commit()

    return CraftResult(
        ok=True,
        result="success",
        card_name=result_card.name
) 
