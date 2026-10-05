"""Декораторы для хендлеров."""

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


def require_role(required: str):
    """Универсальный декоратор по роли."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(query, *args, **kwargs):
            uid = query.from_user.id
            if not await check_role(uid, required):
                await safe_answer(query, "⛔ Нет доступа", show_alert=True)
                return
            return await func(query, *args, **kwargs)
        return wrapper
    return decorator


def require_user(func):
    """Проверяет, что игрок зарегистрирован."""
    @functools.wraps(func)
    async def wrapper(query, *args, **kwargs):
        async with AsyncSessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == query.from_user.id)
            )).scalar_one_or_none()
            if not user:
                await safe_answer(query, "❌ Сначала /start", show_alert=True)
                return
        return await func(query, user=user, *args, **kwargs)
    return wrapper


# Алиасы
require_owner = require_role("owner")
require_admin = require_role("admin")
require_moderator = require_role("moderator")
require_helper = require_role("helper")
require_support = require_role("support") 
