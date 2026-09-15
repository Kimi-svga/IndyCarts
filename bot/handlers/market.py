from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from core.constants import RARITY_EMOJI, MARKET_FEE
from db.session import AsyncSessionLocal
from db.models import Card, User, UserCard

router = Router()


@router.callback_query(MainMenu.filter(F.action == "market"))
async def cb_market(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        stmt = select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        cards = (await session.execute(stmt)).scalars().all()

    text = "💹 <b>Биржа — Топ-10</b>\n\n"
    if not cards:
        text += "Пусто. Админ должен добавить карты."
    else:
        for c in cards:
            emoji = RARITY_EMOJI.get(c.rarity, "⚪")
            text += f"{emoji} <b>#{c.id}</b> {c.name} — {c.current_price} монет\n"
        text += (
            "\n🛒 <code>/buy ID</code> — купить\n"
            "💰 <code>/sell ID</code> — продать свою карту\n"
            f"Комиссия: {int(MARKET_FEE*100)}%"
        )

    await query.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="HTML")


@router.message(F.text.startswith("/buy"))
async def cmd_buy(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/buy ID</code>", parse_mode="HTML")
        return
    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала /start")
            return
        card = (await session.execute(select(Card).where(Card.id == card_id, Card.is_active == True))).scalar_one_or_none()
        if not card:
            await message.answer("❌ Карта не найдена")
            return
        if user.balance < card.current_price:
            await message.answer(f"❌ Не хватает монет. Нужно: {card.current_price}")
            return
        user.balance -= card.current_price
        session.add(UserCard(user_id=user.id, card_id=card.id, acquired_price=card.current_price))
        await session.commit()
        name, price = card.name, card.current_price

    await message.answer(
        f"✅ Куплено: <b>{name}</b> за {price} монет",
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/sell"))
async def cmd_sell(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/sell ID</code> (ID твоей карты из коллекции)", parse_mode="HTML")
        return
    try:
        user_card_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала /start")
            return
        uc = (await session.execute(select(UserCard).where(UserCard.id == user_card_id, UserCard.user_id == user.id))).scalar_one_or_none()
        if not uc:
            await message.answer("❌ У тебя нет такой карты")
            return
        card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
        price = int(card.current_price * (1 - MARKET_FEE))
        user.balance += price
        await session.delete(uc)
        await session.commit()
        name = card.name

    await message.answer(
        f"💰 Продано: <b>{name}</b> за {price} монет (после комиссии)",
        parse_mode="HTML"
    )
