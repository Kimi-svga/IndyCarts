"""Главное меню Simply Flag — совмещение BxB-стиля и кнопок Пьера."""

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Card, User, UserCard


async def build_main_menu_text(
    user: User,
    session: AsyncSession,
) -> str:
    """Инфо-панель в BxB-стиле (блоки с ветками)."""

    cards_count = (await session.execute(
        select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
    )).scalar() or 0

    is_plus_active = (
        user.plus_tier == "indy_plus"
        and user.plus_expires_at is not None
        and user.plus_expires_at > datetime.utcnow()
    )
    plus_status = "✅ активен" if is_plus_active else "❌ не активен"

    common_attempts = user.shop_attempts_today or 0
    free_attempts = user.daily_attempts - common_attempts
    if free_attempts < 0:
        free_attempts = user.daily_attempts
        common_attempts = 0

    daily_status = "доступна сейчас"
    if user.last_daily_at is not None and user.last_daily_at.date() == date.today():
        daily_status = "получена сегодня"

    season_rating = 0

    text = (
        f"📄 <b>МЕНЮ:</b>\n\n"
        f"Здесь собрана основная информация\n"
        f"по вашему профилю.\n\n"
        f"👤 <b>@{user.username}</b> · <code>{user.telegram_id}</code>\n\n"
        f"💰 <b>РЕСУРСЫ</b>\n"
        f"├ Баланс: <b>{user.balance}</b> Simply Coins\n"
        f"├ Карт в коллекции: <b>{cards_count}</b>\n"
        f"└ Попыток: <b>{user.daily_attempts}</b>\n"
        f"  ⬜ Обычные: {common_attempts}\n"
        f"  ⬜ Бесплатные: {free_attempts}\n\n"
        f"🎫 <b>ПОДПИСКА</b>\n"
        f"└ Simply Goat Pass: {plus_status}\n\n"
        f"📊 <b>РЕЙТИНГ</b>\n"
        f"├ Общий: <b>{user.pvp_rating}</b>\n"
        f"└ Сезонный: <b>{season_rating}</b>\n\n"
        f"⏳ Следующая выдача: <b>{daily_status}</b>\n\n"
        f"Выберите нужный раздел ниже."
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
