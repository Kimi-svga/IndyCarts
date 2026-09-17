from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from datetime import date
from bot.keyboards.main import MainMenu, get_main_menu
from bot.keyboards.cards import CardsMenu, get_cards_menu, get_merge_menu
from core.config import settings
from core.constants import RARITY_NAMES, RARITY_EMOJI
from db.session import AsyncSessionLocal
from db.models import User, Card, UserCard
from services.drop import drop_card
from services.merge import merge_cards

router = Router()

@router.callback_query(MainMenu.filter(F.action == "cards"))
async def cb_cards(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text("🃏 <b>Карты</b>", reply_markup=get_cards_menu(), parse_mode="HTML")

@router.callback_query(CardsMenu.filter(F.action == "my"))
async def cb_my(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return
        stmt = select(UserCard, Card).join(Card, UserCard.card_id == Card.id).where(UserCard.user_id == user.id).order_by(UserCard.acquired_at.desc()).limit(10)
        rows = (await session.execute(stmt)).all()
    if not rows:
        text = "🃏 <b>Коллекция пуста</b>"
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
    today = date.today()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return
        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today
            await session.commit()
        if user.daily_attempts <= 0:
            await query.message.edit_text("🎴 <b>Попытки закончились</b>", reply_markup=get_cards_menu(), parse_mode="HTML")
            return
        card, is_iw = await drop_card(session)
        if not card:
            await query.message.edit_text("❌ Нет карт в базе", reply_markup=get_cards_menu(), parse_mode="HTML")
            return
        session.add(UserCard(user_id=user.id, card_id=card.id, is_iw=is_iw, acquired_price=card.current_price))
        user.daily_attempts -= 1
        await session.commit()
        remaining = user.daily_attempts
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    iw_text = " ⭐ <b>INDY WINNER!</b>" if is_iw else ""
    text = f"🎴 <b>Дроп!</b>\n\n{emoji} <b>{card.name}</b>{iw_text}\nРедкость: {RARITY_NAMES[card.rarity]}\nЦена: {card.current_price}\n\nОсталось: <b>{remaining}</b>"
    try:
        await query.message.delete()
    except Exception:
        pass
    if card.image_file_id:
        await query.message.answer_photo(card.image_file_id, caption=text, parse_mode="HTML", reply_markup=get_cards_menu())
    else:
        await query.message.answer(text, reply_markup=get_cards_menu(), parse_mode="HTML")

@router.callback_query(CardsMenu.filter(F.action == "merge"))
async def cb_merge_menu(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🔀 <b>Слияние карт</b>\n\n3 карты → 1 новая (70% успех)\nLegendary → Limited (20%)\n\nВыбери:",
        reply_markup=get_merge_menu(), parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("merge_"))
async def cb_merge(query: CallbackQuery):
    await query.answer()
    rarity = query.data.replace("merge_", "")
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            return
        result = await merge_cards(session, user.id, rarity)
    if not result["ok"]:
        await query.answer(result["reason"], show_alert=True)
        return
    if result["result"] == "burn":
        await query.message.edit_text("❌ <b>Фейл!</b> Карты сгорели.", reply_markup=get_merge_menu(), parse_mode="HTML")
    else:
        await query.message.edit_text(
            f"✅ <b>Успех!</b>\nПолучена: {RARITY_NAMES[result['result']]} — {result['card_name']}",
            reply_markup=get_merge_menu(), parse_mode="HTML"
                                     ) 
