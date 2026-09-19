"""Ежедневная награда."""

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from db.models import DailyReward, User
from db.session import AsyncSessionLocal

router = Router()


@router.callback_query(MainMenu.filter(F.action == "daily"))
async def cb_daily(query: CallbackQuery) -> None:
    """Выдаёт ежедневку (раз в день)."""
    await safe_answer(query)
    today = date.today()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        # Сброс попыток в полночь
        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today

        claimed = (await session.execute(
            select(DailyReward).where(
                DailyReward.user_id == user.id,
                DailyReward.reward_date == today,
            )
        )).scalar_one_or_none()

        if claimed is not None:
            await session.commit()
            await safe_render(query, "🎁 <b>Уже получено сегодня</b>", get_back_menu())
            return

        user.balance += settings.DAILY_MONEY
        user.daily_streak += 1
        user.daily_attempts = settings.DAILY_ATTEMPTS
        user.last_attempt_date = today

        session.add(DailyReward(
            user_id=user.id,
            reward_date=today,
            money=settings.DAILY_MONEY,
            attempts=settings.DAILY_ATTEMPTS,
        ))
        await session.commit()
        streak = user.daily_streak

    await safe_render(
        query,
        f"🎁 <b>Ежедневный бонус</b>\n\n"
        f"💰 +{settings.DAILY_MONEY}\n"
        f"🎴 +{settings.DAILY_ATTEMPTS}\n"
        f"🔥 Стрик: {streak}",
        get_back_menu(),
    ) 
