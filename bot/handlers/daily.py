"""Ежедневная награда."""

from datetime import date, datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from db.models import DailyReward, User
from db.session import AsyncSessionLocal

router = Router()


def _attempts_for(user: User) -> int:
    """Сколько попыток давать игроку (зависит от Indy+)."""
    if user.plus_tier == "indy_plus":
        return settings.PLUS_DAILY_ATTEMPTS
    return settings.DAILY_ATTEMPTS


@router.callback_query(MainMenu.filter(F.action == "daily"))
async def cb_daily(query: CallbackQuery) -> None:
    """Выдаёт ежедневку (раз в день). Если уже получена — таймер."""
    await safe_answer(query)
    today = date.today()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        attempts_grant = _attempts_for(user)

        # Сброс попыток в полночь
        if user.last_attempt_date != today:
            user.daily_attempts = attempts_grant
            user.last_attempt_date = today

        claimed = (await session.execute(
            select(DailyReward).where(
                DailyReward.user_id == user.id,
                DailyReward.reward_date == today,
            )
        )).scalar_one_or_none()

        # Уже получено — таймер
        if claimed is not None:
            await session.commit()

            now = datetime.utcnow()
            tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
            diff = tomorrow - now

            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60

            await safe_render(
                query,
                f"🎁 <b>Ежедневная награда</b>\n\n"
                f"✅ Уже получено сегодня\n\n"
                f"⏳ Следующая через: <b>{hours}ч {minutes}м</b>\n\n"
                f"🔥 Стрик: <b>{user.daily_streak}</b>",
                get_back_menu(),
            )
            return

        # Выдаём
        user.balance += settings.DAILY_MONEY
        user.daily_streak += 1
        user.daily_attempts = attempts_grant
        user.last_attempt_date = today
        user.last_daily_at = datetime.utcnow()

        session.add(DailyReward(
            user_id=user.id,
            reward_date=today,
            money=settings.DAILY_MONEY,
            attempts=attempts_grant,
        ))
        await session.commit()
        streak = user.daily_streak

    await safe_render(
        query,
        f"🎁 <b>Ежедневный бонус</b>\n\n"
        f"💰 +{settings.DAILY_MONEY}\n"
        f"🎴 +{attempts_grant}\n"
        f"🔥 Стрик: {streak}\n\n"
        f"⏳ Следующая через <b>24ч</b>",
        get_back_menu(),
        ) 
