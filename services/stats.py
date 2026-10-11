"""Статистика карт: процент владения, топ редких."""

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import setup_logger
from db.models import Card, User, UserCard

logger = setup_logger()


async def get_ownership(
    session: AsyncSession,
    card_id: int,
) -> dict:
    """
    Возвращает статистику владения картой.

    {
        "owners": 45,
        "total_users": 64,
        "percent": 70.3,
        "copies": 78,       # всего копий в мире
    }
    """
    owners = (await session.execute(
        select(func.count(distinct(UserCard.user_id)))
        .where(UserCard.card_id == card_id)
    )).scalar() or 0

    copies = (await session.execute(
        select(func.count(UserCard.id))
        .where(UserCard.card_id == card_id)
    )).scalar() or 0

    total_users = (await session.execute(
        select(func.count(User.id))
    )).scalar() or 0

    percent = (owners / total_users * 100) if total_users > 0 else 0.0

    return {
        "owners": owners,
        "total_users": total_users,
        "percent": round(percent, 1),
        "copies": copies,
    }


def format_ownership(stats: dict) -> str:
    """Форматирует статистику владения с эмодзи редкости."""
    percent = stats["percent"]
    owners = stats["owners"]
    total = stats["total_users"]

    if percent >= 80:
        emoji = "🟢"  # у всех
    elif percent >= 50:
        emoji = "🟡"  # у большинства
    elif percent >= 25:
        emoji = "🟠"  # у многих
    elif percent >= 10:
        emoji = "🔴"  # редко
    elif percent >= 3:
        emoji = "💎"  # очень редко
    else:
        emoji = "👑"  # легендарно

    return f"{emoji} Владеют: <b>{percent}%</b> ({owners} из {total})"


async def get_rarest_cards(
    session: AsyncSession,
    limit: int = 10,
    min_owners: int = 1,
) -> list[dict]:
    """
    Топ самых редких карт.

    Исключает карты с 0 владельцев (если min_owners=1).
    """
    total_users = (await session.execute(
        select(func.count(User.id))
    )).scalar() or 1

    rows = (await session.execute(
        select(
            Card,
            func.count(distinct(UserCard.user_id)).label("owners"),
            func.count(UserCard.id).label("copies"),
        )
        .join(UserCard, UserCard.card_id == Card.id)
        .where(Card.is_active == True)
        .group_by(Card.id)
        .having(func.count(distinct(UserCard.user_id)) >= min_owners)
        .order_by(
            func.count(distinct(UserCard.user_id)).asc(),
            func.count(UserCard.id).asc(),
        )
        .limit(limit)
    )).all()

    result = []
    for card, owners, copies in rows:
        percent = (owners / total_users * 100) if total_users > 0 else 0.0
        result.append({
            "card": card,
            "owners": owners,
            "copies": copies,
            "percent": round(percent, 1),
        })

    return result
