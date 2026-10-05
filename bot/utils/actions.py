"""Хелпер для логирования действий игроков."""

import json
from typing import Any

from core.logger import setup_logger
from db.models import ActionLog
from db.session import AsyncSessionLocal

logger = setup_logger()


async def log_action(
    user_id: int | None,
    action: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Логирует действие игрока."""
    try:
        async with AsyncSessionLocal() as session:
            session.add(ActionLog(
                user_id=user_id,
                action=action,
                data=json.dumps(data, ensure_ascii=False) if data else None,
            ))
            await session.commit()
    except Exception as e:
        logger.error(f"log_action: {e}")
