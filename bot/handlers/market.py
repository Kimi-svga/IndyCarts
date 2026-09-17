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
        cards = (await session.execute(select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10))).scalars().all()
    text = "💹 <b>Биржа — Топ-10</b>\n\n"
    for c in cards:
        text += f"{RARITY_EMOJI.get(c.rarity, '⚪')} <b>#{c.id}</b> {c.name} — {c.current_price}\n"
    text += f"\n🛒 <code>/buy ID</code>\n💰 <code>/sell ID</code>\nКомиссия: {int(MARKET_FEE*100)}%"
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
        card = (await session.execute(select(Card).where(Card.id == card_id, Card.is_active == True))).scalar_one_or_none()
        if not user or not card:
            await message.answer("❌ Не найдено")
            return
        if user.balance < card.current_price:
            await message.answer(f"❌ Нужно {card.current_price}")
            return
        user.balance -= card.current_price
        session.add(UserCard(user_id=user.id, card_id=card.id, acquired_price=card.current_price))
        await session.commit()
        name, price = card.name, card.current_price
    await message.answer(f"✅ Куплено: <b>{name}</b> за {price}", parse_mode="HTML")

@router.message(F.text.startswith("/sell"))
async def cmd_sell(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/sell ID</code>", parse_mode="HTML")
        return
    try:
        uc_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID — число")
        return
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        uc = (await session.execute(select(UserCard).where(UserCard.id == uc_id, UserCard.user_id == user.id))).scalar_one_or_none()
        if not uc:
            await message.answer("❌ Нет такой карты")
            return
        card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
        price = int(card.current_price * (1 - MARKET_FEE))
        user.balance += price
        await session.delete(uc)
        await session.commit()
        name = card.name
    await message.answer(f"💰 Продано: <b>{name}</b> за {price}", parse_mode="HTML") 
