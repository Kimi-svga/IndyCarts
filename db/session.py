"""Подключение к базе данных. SQLAlchemy 2.0 (async) + asyncpg."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Создаёт таблицы, если их нет."""
    async with engine.begin() as conn:
        from db.models import Base
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрывает движок при остановке."""
    await engine.dispose() 
