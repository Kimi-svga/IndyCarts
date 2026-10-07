"""Middleware — обновляет User.last_seen_at на каждом событии."""

from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select

from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

logger = setup_logger("indycarts.last_seen")


class LastSeenMiddleware(BaseMiddleware):
    """Обновляет last_seen_at у User."""

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
