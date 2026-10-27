"""Middleware — подгружает User в data['user'] (с поддержкой альтов)."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select

from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

logger = setup_logger()


class UserMiddleware(BaseMiddleware):
    """
    Кладёт User в data['user'] для всех хендлеров.
    
    Если у основного юзера active_alt_id != None → кладёт АЛЬТА.
    Иначе → кладёт основного.
    """

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
                main_user = (await session.execute(
                    select(User).where(User.telegram_id == tg_user.id)
                )).scalar_one_or_none()

                # Если основной есть И у него активен альт — берём альта
                if main_user is not None and main_user.active_alt_id is not None:
                    alt = await session.get(User, main_user.active_alt_id)
                    if alt is not None:
                        data["user"] = alt
                        data["main_user"] = main_user
                        data["is_alt_session"] = True
                        return await handler(event, data)

                data["user"] = main_user
                data["main_user"] = main_user
                data["is_alt_session"] = False

        except Exception as e:
            logger.error(f"UserMiddleware: {e}")
            data["user"] = None
            data["main_user"] = None
            data["is_alt_session"] = False

        return await handler(event, data) 
