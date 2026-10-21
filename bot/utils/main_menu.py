"""Сборка текста инфо-панели главного меню."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.constants import CLAN_ROLE_EMOJI, MAIN_MENU_TITLE
from db.models import Badge, Card, Clan, ClanMember, Friend, User, UserBadge, UserCard


async def build_main_menu_text(
    user: User,
    session: AsyncSession,
) -> str:
    """Собирает инфо-панель главного меню."""
    cards_count = (await session.execute(
        select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
    )).scalar() or 0

    collection_value = (await session.execute(
        select(func.sum(Card.current_price))
        .join(UserCard, UserCard.card_id == Card.id)
        .where(UserCard.user_id == user.id)
    )).scalar() or 0

    collection_value = int(collection_value) if collection_value else 0

    friends_count = (await session.execute(
        select(func.count(Friend.id)).where(Friend.user_id == user.id)
    )).scalar() or 0

    # Клан
    clan_line = ""
    row = (await session.execute(
        select(ClanMember, Clan)
        .join(Clan, ClanMember.clan_id == Clan.id)
        .where(ClanMember.user_id == user.id, Clan.is_active == True)
    )).first()

    if row is not None:
        member, clan = row
        emoji = CLAN_ROLE_EMOJI.get(member.role, "👤")
        clan_line = f"\n🏰 [{clan.tag}] {clan.name} · {emoji} ур.{clan.level}"

    daily_status = "доступна"
    if user.last_daily_at is not None:
        if user.last_daily_at.date() == date.today():
            daily_status = "получена"

    # БЕЙДЖИ (визуальные иконки)
    badges = (await session.execute(
        select(Badge)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
    )).scalars().all()
    
    badges_text = ""
    if badges:
        badges_text = " " + "".join(b.icon for b in badges)

    # ТЕКСТОВЫЙ ТИТУЛ (как у Лины)
    title_line = ""
    if user.custom_title:
        title_line = f"\n{user.custom_title}"

    text = (
        f"{MAIN_MENU_TITLE}\n\n"
        f"👤 <b>@{user.username}</b>{badges_text}{title_line}{clan_line}\n"
        f"💰 <b>{user.balance:,}</b>\n"
        f"🃏 <b>{cards_count}</b> карт · 💎 <b>{collection_value:,}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_rating}</b> · 🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"👥 Друзей: <b>{friends_count}</b>\n"
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
