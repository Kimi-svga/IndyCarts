"""Сборка текста инфо-панели главного меню (патч 0.7.0)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MAIN_MENU_TITLE
from db.models import Card, User, UserCard


async def build_main_menu_text(
    user: User,
    session: AsyncSession,
) -> str:
    """
    Собирает инфо-панель главного меню.
    """
    cards_count = (await session.execute(
        select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
    )).scalar() or 0

    collection_value = (await session.execute(
        select(func.sum(Card.current_price))
        .join(UserCard, UserCard.card_id == Card.id)
        .where(UserCard.user_id == user.id)
    )).scalar() or 0

    daily_status = "доступна"
    if user.last_daily_at is not None:
        if user.last_daily_at.date() == date.today():
            daily_status = "получена"

    text = (
        f"{MAIN_MENU_TITLE}\n\n"
        f"👤 <b>@{user.username}</b>\n"
        f"💰 <b>{user.balance:,}</b>\n"
        f"🃏 <b>{cards_count}</b> карт · 💎 <b>{collection_value:,}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_rating}</b> · 🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"🎴 Попытки: <b>{user.daily_attempts}</b>\n"
        f"📅 Ежедневка: <b>{daily_status}</b>"
    )

    return text


async def build_main_menu_text_for(
    session: AsyncSession,
    telegram_id: int,
) -> tuple[str, User | None]:
    """Обёртка — сама находит юзера по telegram_id."""
    user = (await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )).scalar_one_or_none()

    if user is None:
        return "❌ Сначала /start", None

    text = await build_main_menu_text(user, session)
    return text, user
