"""Профиль игрока (с разделом друзей, патч 1.3.0)."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import func, select

from bot.keyboards.main import MainMenu
from bot.keyboards.profile import get_profile_menu
from bot.utils.stable import safe_answer, safe_render
from db.models import Card, Friend, FriendRequest, User, UserCard
from db.session import AsyncSessionLocal

router = Router()


@router.callback_query(MainMenu.filter(F.action == "profile"))
async def cb_profile(query: CallbackQuery) -> None:
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

        friends_count = (await session.execute(
            select(func.count(Friend.id)).where(Friend.user_id == user.id)
        )).scalar() or 0

        incoming_count = (await session.execute(
            select(func.count(FriendRequest.id)).where(
                FriendRequest.to_user_id == user.id,
                FriendRequest.status == "pending",
            )
        )).scalar() or 0

    collection_value = int(collection_value) if collection_value else 0

    text = (
        f"👤 <b>Профиль @{user.username}</b>\n\n"
        f"💰 Баланс: <b>{user.balance:,}</b>\n"
        f"🃏 Карт: <b>{cards_count}</b>\n"
        f"💎 Стоимость коллекции: <b>{collection_value:,}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_rating}</b> ({user.pvp_wins}W/{user.pvp_losses}L)\n"
        f"🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"📈 Доверие: <b>{user.trust_score}</b>\n"
        f"👥 Друзей: <b>{friends_count}</b>"
    )

    await safe_render(query, text, get_profile_menu(friends_count, incoming_count)) 
