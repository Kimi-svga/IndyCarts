"""Уведомления для Visual Merge.

Создаются хуками в боте и API.
Читаются через GET /api/notifications.
Чистятся кроном раз в сутки.
"""

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update

from core.logger import setup_logger
from db.models import Notification
from db.session import AsyncSessionLocal

logger = setup_logger()


# ═════════════════════════════════════════════
# ЦВЕТА ПО ТИПАМ
# ═════════════════════════════════════════════

TYPE_COLORS: dict[str, str] = {
    "broadcast": "blue",
    "pvp":       "orange",
    "trade":     "purple",
    "clan":      "yellow",
    "auction":   "gold",
    "support":   "green",
    "system":    "red",
}

TYPE_ICONS: dict[str, str] = {
    "broadcast": "megaphone",
    "pvp":       "swords",
    "trade":     "repeat",
    "clan":      "shield",
    "auction":   "gavel",
    "support":   "message-circle",
    "system":    "bell",
}


# ═════════════════════════════════════════════
# СОЗДАНИЕ
# ═════════════════════════════════════════════

async def notify(
    session,
    user_id: int,
    type_: str,
    title: str,
    text: str,
    icon: str | None = None,
    color: str | None = None,
    payload: str | None = None,
) -> None:
    """
    Создаёт уведомление в БД.

    ВАЖНО: НЕ коммитит. Коммит делает вызывающий код.
    Так можно делать несколько notify() в одной транзакции.

    Пример:
        await notify(session, user.id, "pvp", "PvP", "@racer вызвал", payload="battle:42")
        await session.commit()
    """
    session.add(Notification(
        user_id=user_id,
        type=type_,
        title=title[:128],
        text=text[:512],
        icon=icon or TYPE_ICONS.get(type_, "bell"),
        color=color or TYPE_COLORS.get(type_, "blue"),
        payload=payload,
        is_read=False,
    ))


async def notify_many(
    session,
    user_ids: list[int],
    type_: str,
    title: str,
    text: str,
    icon: str | None = None,
    color: str | None = None,
    payload: str | None = None,
) -> int:
    """Массовая рассылка (для broadcast). Возвращает количество."""
    icon = icon or TYPE_ICONS.get(type_, "bell")
    color = color or TYPE_COLORS.get(type_, "blue")

    count = 0
    for uid in user_ids:
        session.add(Notification(
            user_id=uid,
            type=type_,
            title=title[:128],
            text=text[:512],
            icon=icon,
            color=color,
            payload=payload,
            is_read=False,
        ))
        count += 1

    return count


# ═════════════════════════════════════════════
# ЧТЕНИЕ
# ═════════════════════════════════════════════

async def get_user_notifications(
    user_id: int,
    limit: int = 30,
) -> list[Notification]:
    """Последние N уведомлений игрока."""
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )).scalars().all()

    return list(rows)


async def get_unread_count(user_id: int) -> int:
    """Сколько непрочитанных."""
    async with AsyncSessionLocal() as session:
        count = (await session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )).scalar() or 0

    return count


# ═════════════════════════════════════════════
# ОТМЕТКА «ПРОЧИТАНО»
# ═════════════════════════════════════════════

async def mark_read(user_id: int, notification_id: int) -> bool:
    """Помечает одно уведомление прочитанным. Возвращает True, если нашли."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        await session.commit()

    return result.rowcount > 0


async def mark_all_read(user_id: int) -> int:
    """Помечает ВСЕ уведомления игрока прочитанными. Возвращает кол-во."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )
        await session.commit()

    return result.rowcount


# ═════════════════════════════════════════════
# ОЧИСТКА
# ═════════════════════════════════════════════

async def clear_user_notifications(user_id: int) -> int:
    """Удаляет ВСЕ уведомления игрока. Возвращает кол-во."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(Notification).where(Notification.user_id == user_id)
        )
        await session.commit()

    return result.rowcount


async def clear_old_notifications(days: int = 1) -> int:
    """
    Удаляет уведомления старше N дней.
    Используется кроном раз в сутки.

    По умолчанию: 1 день (каждый день сброс).
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(Notification).where(Notification.created_at < cutoff)
        )
        await session.commit()

    deleted = result.rowcount
    if deleted:
        logger.info(f"🔔 Удалено уведомлений старше {days}д: {deleted}")

    return deleted
