import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.constants import MERGE_RULES
from db.models import UserCard, Card
from services.drop import get_random_card

async def merge_cards(session: AsyncSession, user_id: int, rarity: str) -> dict:
    if rarity not in MERGE_RULES:
        return {"ok": False, "reason": "Эту редкость нельзя объединить"}
    
    rule = MERGE_RULES[rarity]
    
    stmt = select(UserCard).where(UserCard.user_id == user_id).join(Card, UserCard.card_id == Card.id).where(Card.rarity == rarity).limit(3)
    cards = (await session.execute(stmt)).scalars().all()
    
    if len(cards) < 3:
        return {"ok": False, "reason": f"Нужно 3 карты {rarity}"}
    
    for c in cards:
        await session.delete(c)
    
    roll = random.random()
    if roll < rule["chance"]:
        new_card = await get_random_card(session, rule["result"])
        if new_card:
            session.add(UserCard(user_id=user_id, card_id=new_card.id, acquired_price=new_card.current_price))
            await session.commit()
            return {"ok": True, "result": rule["result"], "card_name": new_card.name, "card_id": new_card.id}
        await session.commit()
        return {"ok": False, "reason": "Нет карт этой редкости в базе"}
    else:
        await session.commit()
        return {"ok": True, "result": "burn", "card_name": None, "card_id": None} 
