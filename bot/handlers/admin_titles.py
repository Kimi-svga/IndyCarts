"""Выдача кастомных титулов (Owner-only)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from core.config import settings
from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


@router.message(Command("settitle"))
async def cmd_set_title(message: Message) -> None:
    """Выдает кастомный титул игроку. Формат: /settitle @username Текст титула"""
    
    # Проверка, что команду вызывает владелец
    if message.from_user.id not in settings.OWNER_IDS:
        return

    # Разбиваем сообщение на 3 части: команда, ник, текст титула (с пробелами)
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Формат: <code>/settitle @username Текст титула</code>\n"
            "Пример: <code>/settitle @Lina 👑 Queen to IndyCarts</code>",
            parse_mode="HTML"
        )
        return

    target_username = parts[1].lstrip("@").lower()
    title_text = parts[2].strip()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target_username)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ Игрок @{target_username} не найден")
            return

        user.custom_title = title_text
        await session.commit()
        
        username = user.username
        target_tg = user.telegram_id

    await message.answer(
        f"✅ Игроку @{username} выдан титул:\n<b>{title_text}</b>",
        parse_mode="HTML"
    )

    # Отправляем уведомление самому игроку
    try:
        await message.bot.send_message(
            target_tg,
            f"👑 <b>Тебе выдан новый титул!</b>\n\n"
            f"Твой профиль теперь украшает: <b>{title_text}</b>\n"
            f"Проверь свой профиль в главном меню!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление о титуле: {e}") 
