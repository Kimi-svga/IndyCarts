"""Indy+ подписка: меню, оплата звёздами, оплата монетами."""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery, LabeledPrice, Message,
    PreCheckoutQuery, SuccessfulPayment,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.logger import setup_logger
from db.models import Subscription, SubscriptionPayment, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()

PLUS_PRICE_STARS = settings.PLUS_PRICE_STARS
PLUS_PRICE_COINS = settings.PLUS_PRICE_COINS
PLUS_DURATION_DAYS = settings.PLUS_DURATION_DAYS


# ─── Меню Indy+ ───

async def _render_plus_menu(query: CallbackQuery) -> None:
    """Рендерит экран Indy+."""
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

    if user is None:
        await safe_render(query, "❌ Сначала /start", get_back_menu())
        return

    is_plus = (
        user.plus_tier == "indy_plus"
        and user.plus_expires_at
        and user.plus_expires_at > datetime.utcnow()
    )

    if is_plus:
        days_left = (user.plus_expires_at - datetime.utcnow()).days
        text = (
            f"💎 <b>Indy+ активна</b>\n\n"
            f"📅 До: <b>{user.plus_expires_at.strftime('%d.%m.%Y')}</b>\n"
            f"⏳ Осталось: <b>{days_left} дней</b>\n\n"
            f"<b>Твои бонусы:</b>\n"
            f"🎴 +{settings.PLUS_BONUS_ATTEMPTS} попыток в день\n"
            f"⚔️ ×{settings.PLUS_PVP_MULTIPLIER} к PvP-рейтингу\n"
            f"💰 Роялти {settings.PLUS_ROYALTY_PERCENT}%\n"
            f"🎯 Комиссия аукциона {settings.PLUS_AUCTION_COMMISSION}%\n"
            f"🍀 +10% к дропу редких\n"
            f"💬 Приоритетная поддержка\n"
            f"🎁 Эксклюзивная карта каждый месяц"
        )
        b = InlineKeyboardBuilder()
        b.button(text=f"💎 Продлить за {PLUS_PRICE_STARS} ⭐", callback_data="plus_buy_stars")
        b.button(text=f"🪙 Продлить за {PLUS_PRICE_COINS:,} монет", callback_data="plus_buy_coins")
        b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
        b.adjust(1)
    else:
        text = (
            f"💎 <b>Indy+</b>\n\n"
            f"Подписка, которая поддерживает проект\n"
            f"и даёт тебе больше возможностей.\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Что даёт Indy+:</b>\n\n"
            f"🎴 <b>+{settings.PLUS_BONUS_ATTEMPTS} попыток в день</b>\n"
            f"Вместо 2 — целых 7. Больше дропа, больше карт.\n\n"
            f"⚔️ <b>×{settings.PLUS_PVP_MULTIPLIER} к PvP-рейтингу</b>\n"
            f"Побеждаешь — получаешь на 20% больше.\n"
            f"Проигрываешь — теряешь на 20% меньше.\n\n"
            f"💰 <b>Роялти {settings.PLUS_ROYALTY_PERCENT}% с авторских карт</b>\n"
            f"Вместо 5%. Когда Creator выйдет — почувствуешь.\n\n"
            f"🎯 <b>Комиссия аукциона {settings.PLUS_AUCTION_COMMISSION}%</b>\n"
            f"Вместо 10%. Продавать выгоднее в 2 раза.\n\n"
            f"🍀 <b>+10% к дропу редких карт</b>\n"
            f"Legendary, Limited — выпадают чаще.\n\n"
            f"🎁 <b>Эксклюзивная карта каждый месяц</b>\n"
            f"Только для подписчиков. Не купить за монеты.\n\n"
            f"💬 <b>Приоритетная поддержка</b>\n"
            f"Твои вопросы — первыми.\n\n"
            f"🎨 <b>Лимит Creator-карт: 10/мес</b>\n"
            f"Вместо 3. Больше творчества.\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Цена:</b>\n"
            f"⭐ <b>{PLUS_PRICE_STARS} звёзд</b> — оплата через Telegram\n"
            f"🪙 или <b>{PLUS_PRICE_COINS:,} монет</b> — внутриигровая валюта\n\n"
            f"<b>Срок:</b> {PLUS_DURATION_DAYS} дней\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💚 <i>Indy+ помогает оплачивать сервера\n"
            f"и разработку новых обновлений.\n"
            f"Спасибо, что поддерживаешь проект.</i>"
        )
        b = InlineKeyboardBuilder()
        b.button(text=f"⭐ Купить за {PLUS_PRICE_STARS} звёзд", callback_data="plus_buy_stars")
        b.button(text=f"🪙 Купить за {PLUS_PRICE_COINS:,} монет", callback_data="plus_buy_coins")
        b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
        b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(F.data == "plus_menu")
async def cb_plus_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    await _render_plus_menu(query)


# ─── Оплата звёздами ───

@router.callback_query(F.data == "plus_buy_stars")
async def cb_plus_buy_stars(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

    if user is None:
        await safe_answer(query, "❌ Сначала /start", show_alert=True)
        return

    payload = f"plus_stars_{user.id}"

    await query.message.answer_invoice(
        title="💎 Indy+",
        description=f"Подписка Indy+ на {PLUS_DURATION_DAYS} дней",
        payload=payload,
        provider_token="",           # ← ПУСТАЯ СТРОКА для цифровых товаров
        currency="XTR",              # ← XTR = Telegram Stars
        prices=[
            LabeledPrice(
                label=f"Indy+ на {PLUS_DURATION_DAYS} дней",
                amount=PLUS_PRICE_STARS,
            ),
        ],
        start_parameter="plus_subscription",
    )


# ─── Pre-Checkout (10 секунд!) ───

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """Подтверждаем платёж. БЕЗ ЗАПРОСОВ К БД."""
    await query.answer(ok=True)


# ─── Успешная оплата ───

@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payment: SuccessfulPayment = message.successful_payment

    payload = payment.invoice_payload
    if not payload.startswith("plus_stars_"):
        logger.warning(f"Неизвестный payload: {payload}")
        return

    try:
        user_id = int(payload.replace("plus_stars_", ""))
    except ValueError:
        logger.error(f"Невалидный payload: {payload}")
        return

    await _activate_plus(
        user_id=user_id,
        method="stars",
        stars_amount=PLUS_PRICE_STARS,
        telegram_payment_id=payment.telegram_payment_charge_id,
        bot=message.bot,
        message=message,
    )


# ─── Оплата монетами ───

@router.callback_query(F.data == "plus_buy_coins")
async def cb_plus_buy_coins(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if user is None:
            return

        if user.balance < PLUS_PRICE_COINS:
            await safe_answer(
                query,
                f"❌ Нужно {PLUS_PRICE_COINS:,} монет. У тебя {user.balance:,}.",
                show_alert=True,
            )
            return

        user.balance -= PLUS_PRICE_COINS
        await session.commit()
        user_id = user.id

    await _activate_plus(
        user_id=user_id,
        method="coins",
        coins_amount=PLUS_PRICE_COINS,
        bot=query.bot,
        callback=query,
    )


# ─── Активация ───

async def _activate_plus(
    user_id: int,
    method: str,
    bot,
    stars_amount: int = 0,
    coins_amount: int = 0,
    telegram_payment_id: str | None = None,
    message: Message | None = None,
    callback: CallbackQuery | None = None,
) -> None:
    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()

        if user is None:
            logger.error(f"User {user_id} не найден")
            return

        if user.plus_expires_at and user.plus_expires_at > now:
            new_expires = user.plus_expires_at + timedelta(days=PLUS_DURATION_DAYS)
        else:
            new_expires = now + timedelta(days=PLUS_DURATION_DAYS)

        user.plus_tier = "indy_plus"
        user.plus_expires_at = new_expires
        user.priority_support = True

        sub = (await session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )).scalar_one_or_none()

        if sub is None:
            session.add(Subscription(
                user_id=user.id,
                tier="indy_plus",
                started_at=now,
                expires_at=new_expires,
                payment_method=method,
                total_paid_stars=stars_amount,
                total_paid_coins=coins_amount,
            ))
        else:
            sub.tier = "indy_plus"
            sub.expires_at = new_expires
            sub.payment_method = method
            sub.renewals_count += 1
            sub.total_paid_stars += stars_amount
            sub.total_paid_coins += coins_amount

        session.add(SubscriptionPayment(
            user_id=user.id,
            method=method,
            amount=stars_amount or coins_amount,
            stars_amount=stars_amount or None,
            telegram_payment_id=telegram_payment_id,
            period_start=now,
            period_end=new_expires,
        ))

        await session.commit()

        user_tg = user.telegram_id
        expires_str = new_expires.strftime("%d.%m.%Y")

    success_text = (
        f"💎 <b>Спасибо за поддержку!</b>\n\n"
        f"Мы очень ценим твою заботу о проекте. "
        f"Indy+ активирована до <b>{expires_str}</b>.\n\n"
        f"Все бонусы уже работают: /plus"
    )

    if message is not None:
        await message.answer(success_text, parse_mode="HTML")
    elif callback is not None:
        await safe_render(callback, success_text, get_back_menu())
    else:
        try:
            await bot.send_message(user_tg, success_text, parse_mode="HTML")
        except Exception:
            pass

    logger.info(f"💎 Indy+ активирован: user_id={user_id}, method={method}") 
