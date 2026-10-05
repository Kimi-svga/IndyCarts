"""Middleware — подгружает User в data['user']."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select

from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

logger = setup_logger()


class UserMiddleware(BaseMiddleware):
    """Кладёт User в data['user'] для всех хендлеров."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        try:
            async with AsyncSessionLocal() as session:
                user = (await session.execute(
                    select(User).where(User.telegram_id == tg_user.id)
                )).scalar_one_or_none()

                data["user"] = user
        except Exception as e:
            logger.error(f"UserMiddleware: {e}")
            data["user"] = None

        return await handler(event, data) 
