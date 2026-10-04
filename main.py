"""Точка входа. FastAPI + aiogram webhook + крон."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from fastapi import FastAPI, Request, Response
from sqlalchemy import func, select

from bot.handlers import (
    admin, bank, cards, daily, market, menu, plus, profile,
    promo, pvp, rating, ref, roles, shop, start,
)
from bot.middlewares.logger import LoggingMiddleware
from core.config import settings
from core.logger import setup_logger
from db.models import Card, Loan, PlusReward, Subscription, User, UserCard
from db.session import AsyncSessionLocal, close_db, init_db

logger = setup_logger()

storage = MemoryStorage()
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=storage)

dp.message.middleware(LoggingMiddleware())
dp.callback_query.middleware(LoggingMiddleware())
dp.callback_query.middleware(CallbackAnswerMiddleware())

for r in (
    start, profile, cards, daily, market, pvp,
    bank, rating, promo, admin, roles, shop, ref,
    plus,
    menu,
):
    dp.include_router(r.router)


# ─── КРОН-ЗАДАЧИ ───

async def save_prices_task() -> None:
    from db.models import PriceHistory
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


async def market_task() -> None:
    from services.economy import Economy
    while True:
        await asyncio.sleep(600)
        try:
            async with AsyncSessionLocal() as session:
                cards_list = (await session.execute(
                    select(Card).where(Card.current_price != Card.base_price)
                )).scalars().all()
                for c in cards_list:
                    c.current_price = Economy.decay_price(c.current_price, c.base_price)
                await session.commit()
                logger.info(f"⏰ Затухание: {len(cards_list)}")
        except Exception as e:
            logger.error(f"Затухание: {e}")


async def loan_check_task() -> None:
    """Каждый час — проверка просрочки кредитов (3 стадии)."""
    from services.bank import apply_trust

    while True:
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()

                # Стадия 1: active → overdue
                to_overdue = (await session.execute(
                    select(Loan).where(
                        Loan.status == "active",
                        Loan.due_at < now,
                    )
                )).scalars().all()

                for loan in to_overdue:
                    loan.status = "overdue"
                    user = await session.get(User, loan.user_id)
                    if user:
                        apply_trust(user, "overdue")
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                "⚠️ <b>ПРОСРОЧКА кредита!</b>\n\n"
                                "3 дня на погашение, иначе:\n"
                                "• Конфискуется 10 карт\n"
                                "• Баланс в минус\n"
                                "• PvP блок на 7 дней",
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass

                # Стадия 2: overdue + 3 дня → defaulted
                to_default = (await session.execute(
                    select(Loan).where(
                        Loan.status == "overdue",
                        Loan.due_at < now - timedelta(days=3),
                    )
                )).scalars().all()

                for loan in to_default:
                    loan.status = "defaulted"
                    user = await session.get(User, loan.user_id)
                    if not user:
                        continue

                    cards = (await session.execute(
                        select(UserCard)
                        .where(UserCard.user_id == user.id)
                        .limit(settings.BANK_OVERDUE_CARDS_CONFISCATE)
                    )).scalars().all()
                    for c in cards:
                        await session.delete(c)

                    remaining = loan.total_due - loan.paid
                    user.balance -= remaining

                    user.pvp_blocked_until = now + timedelta(days=settings.BANK_PVP_BLOCK_DAYS)

                    apply_trust(user, "default")

                    try:
                        await bot.send_message(
                            user.telegram_id,
                            f"🚨 <b>ДЕФОЛТ!</b>\n\n"
                            f"Конфисковано: <b>{len(cards)}</b> карт\n"
                            f"Баланс: <b>{user.balance:,}</b>\n"
                            f"PvP заблокирован на "
                            f"<b>{settings.BANK_PVP_BLOCK_DAYS} дней</b>.",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
                if to_overdue or to_default:
                    logger.info(
                        f"🏦 Просрочка: {len(to_overdue)} → overdue, "
                        f"{len(to_default)} → defaulted"
                    )
        except Exception as e:
            logger.error(f"Кредиты: {e}")


async def pvp_rewards_task() -> None:
    from db.models import PvpReward
    while True:
        await asyncio.sleep(3600)
        now = datetime.utcnow()
        if now.day != 1 or now.hour != 0:
            continue

        try:
            async with AsyncSessionLocal() as session:
                top = (await session.execute(
                    select(User).order_by(User.pvp_rating.desc()).limit(10)
                )).scalars().all()

                rewards = (await session.execute(
                    select(PvpReward).where(PvpReward.is_active == True)
                )).scalars().all()

                reward_map = {r.position: r for r in rewards}

                for i, user in enumerate(top, 1):
                    r = reward_map.get(i)
                    if r is None:
                        continue

                    user.balance += r.reward_money or 0
                    user.daily_attempts += r.reward_attempts or 0

                    card_text = ""
                    if r.reward_card_id:
                        session.add(UserCard(
                            user_id=user.id,
                            card_id=r.reward_card_id,
                            acquired_price=0,
                        ))
                        card_text = "\n🎴 + кастомная карта"

                    try:
                        await bot.send_message(
                            user.telegram_id,
                            f"🏆 <b>Ты в топ-{i} PvP!</b>\n\n"
                            f"💰 +{r.reward_money} монет\n"
                            f"🎴 +{r.reward_attempts} попыток"
                            f"{card_text}",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
                logger.info("🏆 PvP-награды выданы топ-10")
        except Exception as e:
            logger.error(f"PvP-награды: {e}")


async def subscription_check_task() -> None:
    while True:
        await asyncio.sleep(6 * 3600)
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()

                expired = (await session.execute(
                    select(User).where(
                        User.plus_tier == "indy_plus",
                        User.plus_expires_at < now,
                    )
                )).scalars().all()

                for u in expired:
                    u.plus_tier = "free"
                    u.priority_support = False

                    sub = (await session.execute(
                        select(Subscription).where(Subscription.user_id == u.id)
                    )).scalar_one_or_none()
                    if sub:
                        sub.tier = "free"

                    try:
                        await bot.send_message(
                            u.telegram_id,
                            "💎 <b>Indy+ закончилась</b>\n\n"
                            "Продлить: /plus\n\n"
                            "⚠️ Уникальные карты остаются у тебя.",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
                if expired:
                    logger.info(f"💎 Подписки истекли: {len(expired)}")
        except Exception as e:
            logger.error(f"subscription_check: {e}")


async def plus_monthly_rewards_task() -> None:
    while True:
        await asyncio.sleep(3600)
        now = datetime.utcnow()
        if now.day != 1 or now.hour != 0:
            continue

        month = now.strftime("%Y-%m")
        try:
            async with AsyncSessionLocal() as session:
                existing = (await session.execute(
                    select(PlusReward).where(PlusReward.month == month)
                )).scalar_one_or_none()
                if existing:
                    continue

                card = (await session.execute(
                    select(Card)
                    .where(Card.is_plus_only == True, Card.is_active == True)
                    .order_by(func.random())
                    .limit(1)
                )).scalar_one_or_none()

                if card is None:
                    logger.warning("💎 Нет plus-only карты")
                    continue

                session.add(PlusReward(
                    month=month, card_id=card.id,
                    money=5000, attempts=10,
                ))

                subs = (await session.execute(
                    select(User).where(
                        User.plus_tier == "indy_plus",
                        User.plus_expires_at > now,
                    )
                )).scalars().all()

                for u in subs:
                    session.add(UserCard(
                        user_id=u.id, card_id=card.id,
                        acquired_price=0,
                    ))
                    u.balance += 5000
                    u.daily_attempts += 10

                    try:
                        await bot.send_message(
                            u.telegram_id,
                            f"🎁 <b>Ежемесячная награда Indy+</b>\n\n"
                            f"🃏 Эксклюзивная карта: <b>{card.name}</b>\n"
                            f"💰 +5000 монет\n"
                            f"🎴 +10 попыток",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
                logger.info(f"💎 Награды выданы: {len(subs)}")
        except Exception as e:
            logger.error(f"plus_monthly: {e}")


# ─── LIFESPAN ───

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Indy Carts v0.9.0...")

    await init_db()
    asyncio.create_task(save_prices_task())
    asyncio.create_task(market_task())
    asyncio.create_task(loan_check_task())
    asyncio.create_task(pvp_rewards_task())
    asyncio.create_task(subscription_check_task())
    asyncio.create_task(plus_monthly_rewards_task())

    webhook_url = f"{settings.WEBHOOK_URL}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query", "pre_checkout_query"],
    )
    logger.info(f"✅ Вебхук: {webhook_url}")

    yield

    await bot.session.close()
    await close_db()
    logger.info("🛑 Остановлен")


app = FastAPI(title="Indy Carts", version="0.9.0", lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request) -> Response:
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
async def health() -> dict:
    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {
            "status": "ok",
            "version": "0.9.0",
            "bot": me.username,
            "webhook": info.url,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT) 
