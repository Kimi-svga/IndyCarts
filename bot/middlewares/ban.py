"""Middleware — блокирует забаненных."""

from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.utils.stable import safe_answer
from core.logger import setup_logger

logger = setup_logger()


class BanMiddleware(BaseMiddleware):
    """Если user.ban_level == 'ban' → блок."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")

        # Нет user — не зарегистрирован → пропускаем к /start
        if user is None:
            return await handler(event, data)

        # Активный бан?
        if user.ban_level == "ban":
            # Истёк?
            if user.ban_expires_at and user.ban_expires_at < datetime.utcnow():
                # Снимаем автоматически
                try:
                    async with AsyncSessionLocal() as session:
                        fresh = await session.get(User, user.id)
                        if fresh:
                            fresh.ban_level = "none"
                            fresh.ban_expires_at = None
                            await session.commit()
                except Exception:
                    pass
                return await handler(event, data)

            text = "🚫 <b>Ты забанен</b>\n\n"
            if user.ban_expires_at:
                text += f"До: <b>{user.ban_expires_at.strftime('%d.%m.%Y %H:%M')}</b>"
            else:
                text += "<b>Навсегда</b>"

            if isinstance(event, CallbackQuery):
                try:
                    await event.answer(
                        text.replace("<b>", "").replace("</b>", ""),
                        show_alert=True,
                    )
                except Exception:
                    pass
            elif isinstance(event, Message):
                try:
                    await event.answer(text, parse_mode="HTML")
                except Exception:
                    pass
            return None

        # Мьют — флажок
        if user.ban_level == "mute":
            if user.ban_expires_at and user.ban_expires_at < datetime.utcnow():
                return await handler(event, data)
            data["is_muted"] = True

        return await handler(event, data)


# Импорт внизу — чтобы не было циклической зависимости
from db.models import User
from db.session import AsyncSessionLocal 
