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

        if user is None:
            return await handler(event, data)

        if user.ban_level == "ban":
            if user.ban_expires_at and user.ban_expires_at < datetime.utcnow():
                return await handler(event, data)

            text = "🚫 <b>Ты забанен</b>"
            if user.ban_expires_at:
                text += f"\n\nДо: <b>{user.ban_expires_at.strftime('%d.%m.%Y')}</b>"
            else:
                text += "\n\n<b>Навсегда</b>"

            if isinstance(event, CallbackQuery):
                await safe_answer(
                    event,
                    text.replace("<b>", "").replace("</b>", ""),
                    show_alert=True,
                )
            elif isinstance(event, Message):
                await event.answer(text, parse_mode="HTML")
            return None

        if user.ban_level == "mute":
            data["is_muted"] = True

        return await handler(event, data) 
