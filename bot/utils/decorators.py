"""Декораторы для хендлеров. Универсально для Message и CallbackQuery."""

import functools

from sqlalchemy import select

from bot.utils.stable import safe_answer
from core.config import settings
from core.constants import ROLE_LEVELS
from db.models import AdminRole, User
from db.session import AsyncSessionLocal


async def get_user_role(telegram_id: int) -> str | None:
    """Возвращает роль игрока или None."""
    if telegram_id in settings.OWNER_IDS:
        return "owner"

    if telegram_id in settings.ADMIN_IDS:
        return "admin"

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()

        if user is None:
            return None

        role = (await session.execute(
            select(AdminRole).where(
                AdminRole.user_id == user.id,
                AdminRole.is_active == True,
            )
        )).scalar_one_or_none()

    return role.role if role else None


async def check_role(telegram_id: int, required: str) -> bool:
    """Проверяет, что у игрока роль >= required."""
    role = await get_user_role(telegram_id)
    if role is None:
        return False

    user_level = ROLE_LEVELS.get(role, 0)
    required_level = ROLE_LEVELS.get(required, 0)
    return user_level >= required_level


async def _deny(target, text: str = "⛔ Нет доступа") -> None:
    """Универсально отвечает на отказ."""
    if hasattr(target, "answer"):
        # CallbackQuery — есть .answer(text, show_alert)
        if hasattr(target, "data"):  # CallbackQuery
            try:
                await target.answer(text, show_alert=True)
            except Exception:
                pass
        else:  # Message
            try:
                await target.answer(text)
            except Exception:
                pass


def require_role(required: str):
    """Универсальный декоратор по роли."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            uid = event.from_user.id
            if not await check_role(uid, required):
                await _deny(event)
                return
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator


def require_user(func):
    """Проверяет, что игрок зарегистрирован."""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        async with AsyncSessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == event.from_user.id)
            )).scalar_one_or_none()
            if not user:
                await _deny(event, "❌ Сначала /start")
                return
        return await func(event, user=user, *args, **kwargs)
    return wrapper


# Алиасы
require_owner = require_role("owner")
require_admin = require_role("admin")
require_moderator = require_role("moderator")
require_helper = require_role("helper")
require_support = require_role("support") 
