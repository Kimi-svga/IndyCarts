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

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        today = date.today()
        stmt = select(DailyReward).where(
            DailyReward.user_id == user.id,
            DailyReward.reward_date == today
        )
        result = await session.execute(stmt)
        claimed = result.scalar_one_or_none()

        if claimed:
            await query.message.edit_text(
                "🎁 <b>Ежедневка уже получена</b>\n\nВозвращайся завтра!",
                reply_markup=get_back_menu(),
                parse_mode="HTML"
            )
            return

        user.balance += settings.DAILY_MONEY
        user.daily_streak += 1
        reward = DailyReward(
            user_id=user.id,
            reward_date=today,
            money=settings.DAILY_MONEY,
            attempts=settings.DAILY_ATTEMPTS,
        )
        session.add(reward)
        await session.commit()

    await query.message.edit_text(
        f"🎁 <b>Ежедневный бонус</b>\n\n"
        f"💰 +{settings.DAILY_MONEY} монет\n"
        f"🎴 +{settings.DAILY_ATTEMPTS} попытки\n"
        f"🔥 Стрик: {user.daily_streak}",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
  ) 
