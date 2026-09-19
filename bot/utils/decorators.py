"""Декораторы для хендлеров."""

import functools
from sqlalchemy import select

from bot.utils.stable import safe_answer
from db.session import AsyncSessionLocal
from db.models import User, AdminRole
from core.config import settings


def require_user(func):
    """Проверяет, что игрок зарегистрирован, и передаёт его в хендлер."""
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


def require_admin(func):
    """Проверяет, что игрок — админ/владелец."""
    @functools.wraps(func)
    async def wrapper(query, *args, **kwargs):
        uid = query.from_user.id
        if uid in settings.OWNER_IDS or uid in settings.ADMIN_IDS:
            return await func(query, *args, **kwargs)

        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.telegram_id == uid))).scalar_one_or_none()
            if user:
                role = (await session.execute(select(AdminRole).where(AdminRole.user_id == user.id))).scalar_one_or_none()
                if role:
                    return await func(query, *args, **kwargs)

        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
    return wrapper


def require_owner(func):
    """Проверяет, что игрок — владелец."""
    @functools.wraps(func)
    async def wrapper(query, *args, **kwargs):
        if query.from_user.id not in settings.OWNER_IDS:
            await safe_answer(query, "⛔ Только владелец", show_alert=True)
            return
        return await func(query, *args, **kwargs)
    return wrapper 
