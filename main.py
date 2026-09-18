from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Response
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

from core.config import settings
from core.logger import setup_logger
from db.session import init_db, close_db, AsyncSessionLocal
from bot.handlers import start, profile, cards, daily, market, pvp, bank, rating, promo, admin, roles

logger = setup_logger()
storage = MemoryStorage()
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
dp.callback_query.middleware(CallbackAnswerMiddleware())

for r in [start, profile, cards, daily, market, pvp, bank, rating, promo, admin, roles]:
    dp.include_router(r.router)


async def save_prices_task():
    from sqlalchemy import select
    from db.models import Card, PriceHistory
    while True:
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as session:
                cards_list = (await session.execute(select(Card))).scalars().all()
                for c in cards_list:
                    session.add(PriceHistory(card_id=c.id, price=c.current_price))
                await session.commit()
                logger.info(f"📊 История: {len(cards_list)}")
        except Exception as e:
            logger.error(f"История: {e}")


async def market_task():
    from sqlalchemy import select
    from db.models import Card
    from services.economy import decay_price
    while True:
        await asyncio.sleep(600)
        try:
            async with AsyncSessionLocal() as session:
                cards_list = (await session.execute(
                    select(Card).where(Card.current_price != Card.base_price)
                )).scalars().all()
                for c in cards_list:
                    c.current_price = decay_price(c.current_price, c.base_price)
                await session.commit()
                logger.info(f"⏰ Затухание: {len(cards_list)}")
        except Exception as e:
            logger.error(f"Затухание: {e}")


async def loan_check_task():
    from sqlalchemy import select
    from db.models import User, UserCard
    while True:
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                users = (await session.execute(
                    select(User).where(User.loan_amount > 0, User.loan_due_at < now)
                )).scalars().all()
                for u in users:
                    cards_list = (await session.execute(
                        select(UserCard).where(UserCard.user_id == u.id).limit(3)
                    )).scalars().all()
                    for c in cards_list:
                        await session.delete(c)
                    if u.balance >= u.loan_amount:
                        u.balance -= u.loan_amount
                    else:
                        u.balance = 0
                    u.loan_amount = 0
                    u.loan_due_at = None
                    u.trust_score -= 5
                    try:
                        await bot.send_message(
                            u.telegram_id,
                            "⚠️ <b>ПРОСРОЧКА!</b>\n\nБанк забрал твои карты.",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                await session.commit()
                logger.info(f"🏦 Просрочка: {len(users)}")
        except Exception as e:
            logger.error(f"Кредиты: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Indy Carts...")
    await init_db()
    asyncio.create_task(save_prices_task())
    asyncio.create_task(market_task())
    asyncio.create_task(loan_check_task())

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


app = FastAPI(title="Indy Carts", version="0.6.0", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.WEBHOOK_SECRET:
        return Response(status_code=403)
    try:
        data = await request.json()
        update = types.Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"❌ {e}")
    return Response(status_code=200)


@app.get("/health")
async def health():
    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {"status": "ok", "version": "0.6.0", "bot": me.username, "webhook": info.url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT) 
