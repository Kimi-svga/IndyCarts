from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from db.session import AsyncSessionLocal
from db.models import Card
from core.constants import RARITY_EMOJI

router = Router()


@router.callback_query(MainMenu.filter(F.action == "market"))
async def cb_market(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        stmt = select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        result = await session.execute(stmt)
        cards = result.scalars().all()

    if not cards:
        text = "💹 <b>Биржа пуста</b>"
    else:
        text = "💹 <b>Топ-10 карт:</b>\n\n"
        for c in cards:
            emoji = RARITY_EMOJI.get(c.rarity, "⚪")
            iw = " ⭐" if c.is_iw else ""
            text += f"{emoji} <b>{c.name}</b>{iw} — {c.current_price}\n"

    await query.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="HTML") 
