"""Профиль игрока."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from db.models import Card, User, UserCard
from db.session import AsyncSessionLocal

router = Router()


@router.callback_query(MainMenu.filter(F.action == "profile"))
async def cb_profile(query: CallbackQuery) -> None:
    """Показывает профиль."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        cards_count = (await session.execute(
            select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
        )).scalar() or 0

        collection_value = (await session.execute(
            select(func.sum(Card.current_price))
            .join(UserCard, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )).scalar() or 0

    await safe_render(
        query,
        f"👤 <b>Профиль @{user.username}</b>\n\n"
        f"💰 Баланс: <b>{user.balance}</b>\n"
        f"🃏 Карт: <b>{cards_count}</b>\n"
        f"💎 Стоимость коллекции: <b>{collection_value}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_wins}W – {user.pvp_losses}L</b>\n"
        f"🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"📈 Доверие: <b>{user.trust_score}</b>",
        get_back_menu(),
    ) 
