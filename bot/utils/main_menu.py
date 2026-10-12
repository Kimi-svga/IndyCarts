"""Сборка текста инфо-панели главного меню — Simply Flag (BxB-стиль)."""

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import MAIN_MENU_TITLE
from db.models import Card, Clan, ClanMember, Friend, User, UserCard


def _fmt_number(value: int) -> str:
    """Форматирует большие числа: 1.07M, 50.0k, 999."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 10_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:,}"


async def build_main_menu_text(
    user: User,
    session: AsyncSession,
) -> str:
    """Собирает инфо-панель главного меню в стиле BoxBoxBox."""

    # Карты игрока
    cards_count = (await session.execute(
        select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
    )).scalar() or 0

    # Стоимость коллекции
    collection_value = (await session.execute(
        select(func.sum(Card.current_price))
        .join(UserCard, UserCard.card_id == Card.id)
        .where(UserCard.user_id == user.id)
    )).scalar() or 0
    collection_value = int(collection_value) if collection_value else 0

    # Друзья
    friends_count = (await session.execute(
        select(func.count(Friend.id)).where(Friend.user_id == user.id)
    )).scalar() or 0

    # Клан
    clan_line = "—"
    row = (await session.execute(
        select(ClanMember, Clan)
        .join(Clan, ClanMember.clan_id == Clan.id)
        .where(ClanMember.user_id == user.id, Clan.is_active == True)
    )).first()

    if row is not None:
        member, clan = row
        clan_line = f"[{clan.tag}] ур.{clan.level}"

    # Дней в игре
    days_in_game = 0
    if user.created_at is not None:
        days_in_game = (datetime.utcnow() - user.created_at).days

    # Статус дейли
    daily_status = "✅ Получена"
    if user.last_daily_at is None or user.last_daily_at.date() != date.today():
        daily_status = "🎁 Доступна"

    text = (
        f"📊 <b>ИГРОВАЯ СВОДКА:</b>\n\n"
        f"👤 <b>@{user.username}</b> · 🏰 {clan_line}\n\n"
        f"📅 Дней в игре: <b>{days_in_game}</b>\n\n"
        f"💰 <b>РЕСУРСЫ</b>\n"
        f"├ Баланс: <b>{_fmt_number(user.balance)}</b>\n"
        f"├ Попыток: <b>{user.daily_attempts}</b>\n"
        f"└ Карт: <b>{cards_count}</b>\n\n"
        f"💎 <b>КОЛЛЕКЦИЯ</b>\n"
        f"└ Стоимость: <b>{_fmt_number(collection_value)}</b>\n\n"
        f"⚔️ <b>СТАТИСТИКА</b>\n"
        f"├ PvP: <b>{user.pvp_rating}</b>\n"
        f"├ Стрик: <b>{user.daily_streak}</b>\n"
        f"└ Друзей: <b>{friends_count}</b>\n\n"
        f"🎁 <b>ДЕЙЛИ</b>\n"
        f"└ {daily_status}"
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
