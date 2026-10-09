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
from services.clan import get_clan_bonuses, get_user_clan

router = Router()


async def _attempts_for(session, user: User) -> int:
    """Сколько попыток давать игроку за дейли: база + Indy+ + клан."""
    base = (
        settings.PLUS_DAILY_ATTEMPTS
        if user.plus_tier == "indy_plus"
        else settings.DAILY_ATTEMPTS
    )

    clan, _ = await get_user_clan(session, user.id)
    if clan is not None:
        base += get_clan_bonuses(clan.level).extra_attempts

    return base


@router.callback_query(MainMenu.filter(F.action == "daily"))
async def cb_daily(query: CallbackQuery) -> None:
    """Выдаёт ежедневку (раз в день). Не трогает купленные попытки."""
    await safe_answer(query)
    today = date.today()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        claimed = (await session.execute(
            select(DailyReward).where(
                DailyReward.user_id == user.id,
                DailyReward.reward_date == today,
            )
        )).scalar_one_or_none()

        if claimed is not None:
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

        attempts_grant = await _attempts_for(session, user)

        user.balance += settings.DAILY_MONEY
        user.daily_streak += 1
        user.daily_attempts += attempts_grant
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
        total_attempts = user.daily_attempts

    await safe_render(
        query,
        f"🎁 <b>Ежедневный бонус</b>\n\n"
        f"💰 +{settings.DAILY_MONEY}\n"
        f"🎴 +{attempts_grant} попыток\n"
        f"🔥 Стрик: <b>{streak}</b>\n\n"
        f"🎴 Всего попыток: <b>{total_attempts}</b>\n"
        f"⏳ Следующая через <b>24ч</b>",
        get_back_menu(),
    ) 
