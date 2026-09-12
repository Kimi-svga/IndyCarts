from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import settings
from core.logger import setup_logger
from db.session import init_db, close_db
from bot.handlers import start, profile, cards, daily, market, pvp, bank, rating, admin

logger = setup_logger()

storage = MemoryStorage()
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=storage)

dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(cards.router)
dp.include_router(daily.router)
dp.include_router(market.router)
dp.include_router(pvp.router)
dp.include_router(bank.router)
dp.include_router(rating.router)
dp.include_router(admin.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Indy Carts...")
    await init_db()

    webhook_url = f"{settings.WEBHOOK_URL}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )
    logger.info(f"✅ Вебхук: {webhook_url}")

    yield

    await bot.session.close()
    await close_db()
    logger.info("🛑 Остановлен")


app = FastAPI(title="Indy Carts", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
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
    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {"status": "ok", "bot": me.username, "webhook": info.url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
