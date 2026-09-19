"""Магазин попыток."""

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu
from bot.keyboards.shop import ShopMenu, get_shop_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from db.models import User
from db.session import AsyncSessionLocal

router = Router()


@router.callback_query(MainMenu.filter(F.action == "shop"))
async def cb_shop(query: CallbackQuery) -> None:
    """Открывает магазин."""
    await safe_answer(query)
    rate = settings.SHOP_COIN_PER_ATTEMPT * 2
    await safe_render(
        query,
        f"🛒 <b>Магазин</b>\n\n"
        f"Курс: <b>{rate} монет = 2 попытки</b>\n"
        f"({settings.SHOP_COIN_PER_ATTEMPT} монет за 1 попытку)\n"
        f"Лимит: {settings.MAX_ATTEMPTS_PER_DAY} попыток в день\n\n"
        f"Выбери пакет:",
        get_shop_menu(),
    )


@router.callback_query(ShopMenu.filter(F.action == "buy"))
async def cb_shop_buy(query: CallbackQuery, callback_data: ShopMenu) -> None:
    """Покупка попыток."""
    await safe_answer(query)
    attempts = callback_data.amount
    cost = attempts * settings.SHOP_COIN_PER_ATTEMPT

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        today = date.today()
        if user.last_shop_date != today:
            user.shop_attempts_today = 0
            user.last_shop_date = today

        if user.shop_attempts_today + attempts > settings.MAX_ATTEMPTS_PER_DAY:
            await safe_answer(
                query,
                f"❌ Лимит {settings.MAX_ATTEMPTS_PER_DAY} попыток в день",
                show_alert=True,
            )
            return

        if user.balance < cost:
            await safe_answer(query, f"❌ Нужно {cost} монет", show_alert=True)
            return

        user.balance -= cost
        user.daily_attempts += attempts
        user.shop_attempts_today += attempts
        await session.commit()

        balance = user.balance
        total_attempts = user.daily_attempts

    await safe_render(
        query,
        f"✅ <b>Куплено!</b>\n\n"
        f"🎴 +{attempts} попыток\n"
        f"💰 -{cost} монет\n\n"
        f"Осталось: <b>{balance}</b> монет\n"
        f"Попыток: <b>{total_attempts}</b>",
        get_shop_menu(),
    )
