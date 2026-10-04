"""Middleware для логирования ВСЕХ событий в боте."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from core.logger import setup_logger

logger = setup_logger()


class LoggingMiddleware(BaseMiddleware):
    """Логирует все сообщения и колбэки."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Логируем сообщения
        if isinstance(event, Message):
            user = event.from_user
            text = event.text or event.caption or "[медиа]"
            logger.info(
                f"📨 @{user.username or user.id} | "
                f"текст: {text[:50]}"
            )

        # Логируем колбэки
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(
                f"🔘 @{user.username or user.id} | "
                f"нажал: {event.data}"
            )

        return await handler(event, data)
