"""Управление бейджами (создание и выдача)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from core.config import settings
from core.logger import setup_logger
from db.models import Badge, User, UserBadge
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()

@router.message(Command("create_badge"))
async def cmd_create_badge(message: Message) -> None:
    """Создать бейдж: /create_badge code "Название" "Иконка" "Описание" """
    if message.from_user.id not in settings.OWNER_IDS:
        return

    # Формат: /create_badge queen "Королева" "👑" "Собрал все карты"
    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        await message.answer(
            "Формат: <code>/create_badge код \"Название\" \"Эмодзи\" \"Описание\"</code>",
            parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    name = parts[2].strip('"')
    icon = parts[3].strip('"')
    desc = parts[4].strip('"')

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(Badge).where(Badge.code == code)
        )).scalar_one_or_none()

        if existing:
            await message.answer("❌ Бейдж с таким кодом уже существует")
            return

        session.add(Badge(code=code, name=name, icon=icon, description=desc))
        await session.commit()

    await message.answer(f"✅ Бейдж создан: {icon} {name}")


@router.message(Command("give_badge"))
async def cmd_give_badge(message: Message) -> None:
    """Выдать бейдж: /give_badge @username code"""
    if message.from_user.id not in settings.OWNER_IDS:
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>/give_badge @username code</code>", parse_mode="HTML")
        return

    target_username = parts[1].lstrip("@").lower()
    badge_code = parts[2].strip()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target_username)
        )).scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Игрок @{target_username} не найден")
            return

        badge = (await session.execute(
            select(Badge).where(Badge.code == badge_code)
        )).scalar_one_or_none()

        if not badge:
            await message.answer(f"❌ Бейдж с кодом '{badge_code}' не найден")
            return

        # Проверяем, нет ли уже
        existing = (await session.execute(
            select(UserBadge).where(
                UserBadge.user_id == user.id,
                UserBadge.badge_id == badge.id
            )
        )).scalar_one_or_none()

        if existing:
            await message.answer("❌ У игрока уже есть этот бейдж")
            return

        session.add(UserBadge(user_id=user.id, badge_id=badge.id))
        await session.commit()

        username = user.username
        target_tg = user.telegram_id

    await message.answer(f"✅ Бейдж {badge.icon} {badge.name} выдан @{username}")

    try:
        await message.bot.send_message(
            target_tg,
            f"🏅 <b>Ты получил новый бейдж!</b>\n\n"
            f"{badge.icon} <b>{badge.name}</b>\n"
            f"<i>{badge.description}</i>",
            parse_mode="HTML"
        )
    except Exception:
        pass
