from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import date
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings
from db.session import AsyncSessionLocal
from db.models import User, DailyReward

router = Router()


@router.callback_query(MainMenu.filter(F.action == "daily"))
async def cb_daily(query: CallbackQuery):
    await query.answer()
    tg_id = query.from_user.id
    today = date.today()

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today

        stmt = select(DailyReward).where(
            DailyReward.user_id == user.id,
            DailyReward.reward_date == today
        )
        claimed = (await session.execute(stmt)).scalar_one_or_none()

        if claimed:
            await session.commit()
            await query.message.edit_text(
                "🎁 <b>Уже получено сегодня</b>\n\n"
                f"🎴 Попытки: {user.daily_attempts}\n"
                "Возвращайся завтра!",
                reply_markup=get_back_menu(),
                parse_mode="HTML"
            )
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

    await query.message.edit_text(
        f"🎁 <b>Ежедневный бонус</b>\n\n"
        f"💰 +{settings.DAILY_MONEY} монет\n"
        f"🎴 +{settings.DAILY_ATTEMPTS} попытки\n"
        f"🔥 Стрик: {user.daily_streak}",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
        ) 
