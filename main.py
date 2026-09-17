"""
Indy Carts — точка входа.
FastAPI + aiogram 3 webhook + SQLAlchemy async.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import select

from core.config import settings
from core.logger import setup_logger
from db.session import init_db, close_db, AsyncSessionLocal
from db.models import Card
from services.economy import decay_price

# Импорт всех роутеров
from bot.handlers import (
    start, profile, cards, daily, market,
    pvp, bank, rating, promo, admin
)

logger = setup_logger()

# FSM storage (в памяти — сбрасывается при рестарте, но это ок для MVP)
storage = MemoryStorage()

# Бот
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Диспетчер
dp = Dispatcher(storage=storage)

# Подключаем роутеры
dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(cards.router)
dp.include_router(daily.router)
dp.include_router(market.router)
dp.include_router(pvp.router)
dp.include_router(bank.router)
dp.include_router(rating.router)
dp.include_router(promo.router)
dp.include_router(admin.router)


async def market_decay_task():
    """
    Фоновая задача: каждый час плавно возвращает цены к базовым.
    Работает вечно, пока бот запущен.
    """
    while True:
        await asyncio.sleep(3600)  # 1 час
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(Card).where(Card.current_price != Card.base_price)
                cards = (await session.execute(stmt)).scalars().all()

                for card in cards:
                    card.current_price = decay_price(
                        card.current_price,
                        card.base_price
                    )

                await session.commit()
                logger.info(f"⏰ Затухание: обработано {len(cards)} карт")
        except Exception as e:
            logger.error(f"❌ Ошибка затухания: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Запуск и остановка приложения."""
    logger.info("🚀 Запуск Indy Carts v0.6...")

    # Инициализация БД
    await init_db()

    # Запуск фоновой задачи затухания
    asyncio.create_task(market_decay_task())

    # Установка вебхука
    webhook_url = f"{settings.WEBHOOK_URL}/webhook"
    try:
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
        )
        logger.info(f"✅ Вебхук: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")

    yield

    # Остановка
    await bot.session.close()
    await close_db()
    logger.info("🛑 Indy Carts остановлен")


app = FastAPI(title="Indy Carts", version="0.6.0", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    """Обработка вебхуков от Telegram."""
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != settings.WEBHOOK_SECRET:
        return Response(status_code=403)

    try:
        data = await request.json()
        update = types.Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"❌ Ошибка update: {e}")

    return Response(status_code=200)


@app.get("/health")
async def health():
    """Health-check для пингера."""
    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {
            "status": "ok",
            "version": "0.6.0",
            "bot": me.username,
            "webhook": info.url,
            "pending": info.pending_update_count,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {"status": "Indy Carts is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT) 
