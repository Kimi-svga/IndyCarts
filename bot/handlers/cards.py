from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from db.session import AsyncSessionLocal
from db.models import User, Card, UserCard
from core.constants import RARITY_EMOJI

router = Router()


@router.callback_query(MainMenu.filter(F.action == "cards"))
async def cb_cards(query: CallbackQuery):
    await query.answer()
    tg_id = query.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
            .limit(10)
        )
        result = await session.execute(stmt)
        rows = result.all()

    if not rows:
        text = "🃏 <b>Коллекция пуста</b>"
    else:
        text = f"🃏 <b>Твои карты</b> ({len(rows)}):\n\n"
        for uc, card in rows:
            emoji = RARITY_EMOJI.get(card.rarity, "⚪")
            iw = " ⭐" if card.is_iw else ""
            text += f"{emoji} <b>{card.name}</b>{iw} — {card.current_price}\n"

    await query.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="HTML")
