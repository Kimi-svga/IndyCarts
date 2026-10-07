"""Middleware: логирование update + last_seen_at."""

import time
from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

logger = setup_logger("updo.middleware")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        uid = user.id if user else "?"
        uname = getattr(user, "username", None) or "—"

        if isinstance(event, Message):
            text = (event.text or event.caption or "[non-text]")[:60]
            logger.info(f"📨 MESSAGE uid={uid} @{uname} chat={event.chat.type} text={text!r}")
        elif isinstance(event, CallbackQuery):
            logger.info(f"🔘 CALLBACK uid={uid} @{uname} data={event.data!r}")
        else:
            logger.info(f"❔ EVENT type={type(event).__name__} uid={uid}")

        start = time.monotonic()
        try:
            result = await handler(event, data)
            dur = (time.monotonic() - start) * 1000
            logger.debug(f"✅ HANDLED uid={uid} in {dur:.0f}ms")
            return result
        except Exception as e:
            dur = (time.monotonic() - start) * 1000
            logger.exception(f"❌ ERROR uid={uid} in {dur:.0f}ms: {e}")
            raise


class LastSeenMiddleware(BaseMiddleware):
    """Обновляет User.last_seen_at на каждом событии."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            try:
                async with AsyncSessionLocal() as session:
                    db_user = (await session.execute(
                        select(User).where(User.telegram_id == user.id)
                    )).scalar_one_or_none()
                    if db_user:
                        db_user.last_seen_at = datetime.utcnow()
                        await session.commit()
            except Exception as e:
                logger.error(f"last_seen: {e}")

        return await handler(event, data)
