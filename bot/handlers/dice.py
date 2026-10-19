"""Кубик раз в 7 дней."""

import random
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from db.models import User
from db.session import AsyncSessionLocal

router = Router()

@router.callback_query(MainMenu.filter(F.action == "dice"))
async def cb_dice(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        # Блокируем строку пользователя, чтобы двойной клик не выдал две награды
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        now = datetime.utcnow()
        
        # Проверка кулдауна (7 дней)
        if user.last_dice_at is not None:
            time_passed = now - user.last_dice_at
            if time_passed.days < 7:
                days_left = 7 - time_passed.days
                await safe_render(
                    query,
                    f"🎲 <b>Кубик уже брошен!</b>\n\n"
                    f"⏳ Следующий кубик через: <b>{days_left} дн.</b>\n\n"
                    f"💡 Заходи в бота почаще, чтобы не пропустить!",
                    get_back_menu()
                )
                return

        # Бросок кубика (от 1 до 6)
        roll = random.randint(1, 6)
        
        # Начисляем попытки
        user.daily_attempts += roll
        user.last_dice_at = now
        
        await session.commit()
        total_attempts = user.daily_attempts

    # Красивая визуализация выпавшего числа
    dice_emojis = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣"}
    emoji = dice_emojis.get(roll, "🎲")

    await safe_render(
        query,
        f"🎲 <b>Ты бросил кубик!</b>\n\n"
        f"Выпало: {emoji} <b>{roll}</b>\n\n"
        f"🎴 Начислено попыток: <b>+{roll}</b>\n"
        f"🎴 Всего попыток: <b>{total_attempts}</b>\n\n"
        f"<i>Следующий кубик будет доступен через 7 дней.</i>",
        get_back_menu()
) 
