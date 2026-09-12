from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func

from bot.keyboards.main import MainMenu, get_back_menu
from db.session import AsyncSessionLocal
from db.models import User, UserCard

router = Router()


@router.callback_query(MainMenu.filter(F.action == "profile"))
async def cb_profile(query: CallbackQuery):
    await query.answer()
    tg_id = query.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        stmt_cards = select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
        result_cards = await session.execute(stmt_cards)
        cards_count = result_cards.scalar() or 0

    await query.message.edit_text(
        f"👤 <b>Профиль @{user.username}</b>\n\n"
        f"💰 Баланс: <b>{user.balance}</b>\n"
        f"🃏 Карт: <b>{cards_count}</b>\n"
        f"🏆 Рейтинг: <b>{user.rating_total}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_wins}W – {user.pvp_losses}L</b>",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
  ) 
