from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from datetime import date

from bot.keyboards.main import MainMenu, get_main_menu
from bot.keyboards.cards import CardsMenu, get_cards_menu
from core.config import settings
from core.constants import RARITY_NAMES, RARITY_EMOJI
from db.session import AsyncSessionLocal
from db.models import User, Card, UserCard
from services.drop import drop_card

router = Router()


@router.callback_query(MainMenu.filter(F.action == "cards"))
async def cb_cards(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🃏 <b>Карты</b>\n\nВыбери действие:",
        reply_markup=get_cards_menu(),
        parse_mode="HTML"
    )


@router.callback_query(CardsMenu.filter(F.action == "my"))
async def cb_my_cards(query: CallbackQuery):
    await query.answer()
    tg_id = query.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
            .order_by(UserCard.acquired_at.desc())
            .limit(10)
        )
        rows = (await session.execute(stmt)).all()

    if not rows:
        text = "🃏 <b>Коллекция пуста</b>\n\nНажми «Дроп»."
    else:
        text = "🃏 <b>Твои карты</b>:\n\n"
        for uc, card in rows:
            emoji = RARITY_EMOJI.get(card.rarity, "⚪")
            iw = " ⭐ IW" if uc.is_iw else ""
            text += f"{emoji} <b>{card.name}</b>{iw} — {card.current_price}\n"

    await query.message.edit_text(text, reply_markup=get_cards_menu(), parse_mode="HTML")


@router.callback_query(CardsMenu.filter(F.action == "drop"))
async def cb_drop(query: CallbackQuery):
    await query.answer()
    tg_id = query.from_user.id
    today = date.today()

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return

        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today
            await session.commit()

        if user.daily_attempts <= 0:
            await query.message.edit_text(
                "🎴 <b>Попытки закончились</b>\n\nВозвращайся завтра!",
                reply_markup=get_cards_menu(),
                parse_mode="HTML"
            )
            return

        card, is_iw = await drop_card(session)
        if not card:
            await query.message.edit_text(
                "❌ В базе нет карт. Админ должен добавить через /addcard.",
                reply_markup=get_cards_menu(),
                parse_mode="HTML"
            )
            return

        user_card = UserCard(
            user_id=user.id,
            card_id=card.id,
            is_iw=is_iw,
            acquired_price=card.current_price,
        )
        session.add(user_card)
        user.daily_attempts -= 1
        await session.commit()
        remaining = user.daily_attempts

    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    iw_text = " ⭐ <b>INDY WINNER!</b>" if is_iw else ""
    text = (
        f"🎴 <b>Дроп!</b>\n\n"
        f"{emoji} <b>{card.name}</b>{iw_text}\n"
        f"Редкость: {RARITY_NAMES[card.rarity]}\n"
        f"Цена: {card.current_price}\n\n"
        f"Осталось попыток: <b>{remaining}</b>"
    )

    try:
        await query.message.delete()
    except Exception:
        pass

    if card.image_file_id:
        await query.message.answer_photo(
            card.image_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_cards_menu()
        )
    else:
        await query.message.answer(text, reply_markup=get_cards_menu(), parse_mode="HTML")


@router.callback_query(CardsMenu.filter(F.action == "back"))
async def cb_cards_back(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🏁 <b>Главное меню</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
