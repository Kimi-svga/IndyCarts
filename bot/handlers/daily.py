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
    today = date.today()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return
        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today
        claimed = (await session.execute(select(DailyReward).where(DailyReward.user_id == user.id, DailyReward.reward_date == today))).scalar_one_or_none()
        if claimed:
            await session.commit()
            await query.message.edit_text("🎁 <b>Уже получено сегодня</b>", reply_markup=get_back_menu(), parse_mode="HTML")
            return
        user.balance += settings.DAILY_MONEY
        user.daily_streak += 1
        user.daily_attempts = settings.DAILY_ATTEMPTS
        user.last_attempt_date = today
        session.add(DailyReward(user_id=user.id, reward_date=today, money=settings.DAILY_MONEY, attempts=settings.DAILY_ATTEMPTS))
        await session.commit()
    await query.message.edit_text(
        f"🎁 <b>Ежедневный бонус</b>\n\n💰 +{settings.DAILY_MONEY}\n🎴 +{settings.DAILY_ATTEMPTS}\n🔥 Стрик: {user.daily_streak}",
        reply_markup=get_back_menu(), parse_mode="HTML"
    ) 
