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
from core.constants import PVP_SEASON_REWARDS
from core.logger import setup_logger
from db.models import (
    Card, Loan, PlusReward, PvpBattle, PvpSeason, SeasonReward,
    Subscription, User, UserCard, UserSeasonStat,
)
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
    from services.bank import apply_trust
    while True:
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()

                to_overdue = (await session.execute(
                    select(Loan).where(Loan.status == "active", Loan.due_at < now)
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
                                "3 дня на погашение, иначе дефолт.",
                                parse_mode="HTML",
                            )
                        except Exception:
                            pass

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
                            f"PvP заблокирован на <b>{settings.BANK_PVP_BLOCK_DAYS} дней</b>.",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
        except Exception as e:
            logger.error(f"Кредиты: {e}")


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
                            "💎 <b>Indy+ закончилась</b>\n\nПродлить: /plus",
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
                    .order_by(func.random()).limit(1)
                )).scalar_one_or_none()

                if card is None:
                    continue

                session.add(PlusReward(month=month, card_id=card.id, money=5000, attempts=10))

                subs = (await session.execute(
                    select(User).where(
                        User.plus_tier == "indy_plus",
                        User.plus_expires_at > now,
                    )
                )).scalars().all()

                for u in subs:
                    session.add(UserCard(user_id=u.id, card_id=card.id, acquired_price=0))
                    u.balance += 5000
                    u.daily_attempts += 10
                    try:
                        await bot.send_message(
                            u.telegram_id,
                            f"🎁 <b>Награда Indy+</b>\n\n"
                            f"🃏 {card.name}\n💰 +5000\n🎴 +10",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

                await session.commit()
        except Exception as e:
            logger.error(f"plus_monthly: {e}")


async def pvp_season_task() -> None:
    """Проверяет сезон каждый час. Если кончился — завершает и выдаёт награды."""
    while True:
        await asyncio.sleep(3600)
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()

                season = (await session.execute(
                    select(PvpSeason).where(PvpSeason.is_active == True)
                )).scalar_one_or_none()

                if season is None:
                    # Создать первый сезон, если нет
                    session.add(PvpSeason(
                        number=1,
                        name="Сезон 1",
                        starts_at=now,
                        ends_at=now + timedelta(days=settings.PVP_SEASON_DAYS),
                        is_active=True,
                    ))
                    await session.commit()
                    logger.info("🏁 Создан первый сезон PvP")
                    continue

                # Ещё не кончился
                if season.ends_at > now:
                    continue

                # ── Сезон закончился ──
                logger.info(f"🏁 Завершение сезона S{season.number}")

                # 1. Топ-10
                top = (await session.execute(
                    select(User).order_by(User.pvp_rating.desc()).limit(10)
                )).scalars().all()

                # 2. Снимок
                import json
                snapshot = [
                    {"id": u.id, "username": u.username, "rating": u.pvp_rating}
                    for u in top
                ]
                season.top10_snapshot = json.dumps(snapshot)

                # 3. Награды из БД (если настроены) или из констант
                rewards_db = (await session.execute(
                    select(SeasonReward).where(SeasonReward.season_id == season.id)
                )).scalars().all()
                rewards_map = {r.position: r for r in rewards_db}

                for i, user in enumerate(top, 1):
                    r = rewards_map.get(i)

                    money = r.reward_money if r else PVP_SEASON_REWARDS.get(i, {}).get("money", 0)
                    attempts = r.reward_attempts if r else PVP_SEASON_REWARDS.get(i, {}).get("attempts", 0)
                    card_id = r.reward_card_id if r else None
                    title = r.title if r else PVP_SEASON_REWARDS.get(i, {}).get("title")

                    user.balance += money
                    user.daily_attempts += attempts

                    if card_id:
                        session.add(UserCard(user_id=user.id, card_id=card_id, acquired_price=0))

                    # Титул
                    if title:
                        import json as js
                        try:
                            titles = js.loads(user.season_titles or "[]")
                        except Exception:
                            titles = []
                        titles.append(f"{title} S{season.number}")
                        user.season_titles = js.dumps(titles, ensure_ascii=False)

                    # Лучший результат
                    if user.best_rank is None or i < user.best_rank:
                        user.best_rank = i
                    if user.best_rating is None or user.pvp_rating > user.best_rating:
                        user.best_rating = user.pvp_rating

                    user.seasons_played += 1

                    # Статистика сезона
                    session.add(UserSeasonStat(
                        user_id=user.id,
                        season_id=season.id,
                        final_rank=i,
                        final_rating=user.pvp_rating,
                        reward_received=money,
                    ))

                    # Уведомление
                    text = (
                        f"🏆 <b>Сезон S{season.number} завершён!</b>\n\n"
                        f"Твоё место: <b>#{i}</b>\n"
                        f"Рейтинг: <b>{user.pvp_rating}</b>\n\n"
                        f"💰 +{money:,} монет\n"
                        f"🎴 +{attempts} попыток"
                    )
                    if card_id:
                        text += "\n🃏 +эксклюзивная карта"
                    if title:
                        text += f"\n🏅 Титул: <b>{title} S{season.number}</b>"

                    try:
                        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
                    except Exception:
                        pass

                # 4. Сброс рейтинга ВСЕМ
                all_users = (await session.execute(select(User))).scalars().all()
                for u in all_users:
                    u.pvp_rating = settings.PVP_SEASON_RESET_RATING
                    u.pvp_wins = 0
                    u.pvp_losses = 0

                # 5. Закрыть старый
                season.is_active = False
                season.is_finished = True

                # 6. Создать новый
                new_season = PvpSeason(
                    number=season.number + 1,
                    name=f"Сезон {season.number + 1}",
                    starts_at=now,
                    ends_at=now + timedelta(days=settings.PVP_SEASON_DAYS),
                    is_active=True,
                )
                session.add(new_season)

                await session.commit()
                logger.info(f"🏁 S{season.number} завершён. S{season.number + 1} начат.")

        except Exception as e:
            logger.error(f"pvp_season: {e}")


async def pvp_timeout_task() -> None:
    """Каждые 5 минут — отменяет зависшие бои."""
    while True:
        await asyncio.sleep(300)
        try:
            async with AsyncSessionLocal() as session:
                cutoff = datetime.utcnow() - timedelta(minutes=settings.PVP_TIMEOUT_MINUTES)

                stuck = (await session.execute(
                    select(PvpBattle).where(
                        PvpBattle.status == "pending",
                        PvpBattle.created_at < cutoff,
                    )
                )).scalars().all()

                for battle in stuck:
                    battle.status = "expired"

                    # Разблокировать карты
                    stakes = (await session.execute(
                        select(PvpStake).where(PvpStake.battle_id == battle.id)
                    )).scalars().all()

                    for stake in stakes:
                        uc = await session.get(UserCard, stake.user_card_id)
                        if uc:
                            uc.is_locked = False

                await session.commit()
                if stuck:
                    logger.info(f"⏰ Зависших боёв отменено: {len(stuck)}")
        except Exception as e:
            logger.error(f"pvp_timeout: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск Indy Carts v1.0.0...")

    await init_db()
    asyncio.create_task(save_prices_task())
    asyncio.create_task(market_task())
    asyncio.create_task(loan_check_task())
    asyncio.create_task(subscription_check_task())
    asyncio.create_task(plus_monthly_rewards_task())
    asyncio.create_task(pvp_season_task())
    asyncio.create_task(pvp_timeout_task())

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


app = FastAPI(title="Indy Carts", version="1.0.0", lifespan=lifespan)


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
            "version": "1.0.0",
            "bot": me.username,
            "webhook": info.url,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT) 
