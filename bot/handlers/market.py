from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from core.constants import RARITY_EMOJI, RARITY_NAMES
from db.session import AsyncSessionLocal
from db.models import Card, User, UserCard
from services.economy import get_price_change, format_change

router = Router()


@router.callback_query(MainMenu.filter(F.action == "market"))
async def cb_market(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        )).scalars().all()
    if not cards:
        await query.message.edit_text("💹 <b>Биржа пуста</b>", reply_markup=get_back_menu(), parse_mode="HTML")
        return
    await show_market_card(query, cards, 0)


async def show_market_card(query: CallbackQuery, cards: list, index: int):
    card = cards[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    async with AsyncSessionLocal() as session:
        change = await get_price_change(session, card.id, hours=24)
    change_text = format_change(change)
    limit_text = ""
    if card.max_supply:
        limit_text = f"\n📜 Тираж: <b>{card.issued}/{card.max_supply}</b>"
    text = (
        f"💹 <b>{card.name}</b>\n"
        f"Редкость: {RARITY_NAMES[card.rarity]} {emoji}\n"
        f"Команда: {card.team or '—'}\n"
        f"Цена: <b>{card.current_price}</b> монет {change_text}{limit_text}\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(cards)}</b>"
    )
    builder = InlineKeyboardBuilder()
    if index > 0:
        builder.button(text="⬅️", callback_data=f"mkt_{index - 1}")
    builder.button(text=f"{index + 1}/{len(cards)}", callback_data="noop")
    if index < len(cards) - 1:
        builder.button(text="➡️", callback_data=f"mkt_{index + 1}")
    builder.button(text="💰 Купить", callback_data=f"buy_{card.id}")
    builder.button(text="📊 Индекс", callback_data=f"index_{card.id}")
    builder.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    builder.adjust(3, 1, 1, 1)
    try:
        await query.message.delete()
    except Exception:
        pass
    if card.image_file_id:
        await query.message.answer_photo(card.image_file_id, caption=text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await query.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("mkt_"))
async def cb_market_nav(query: CallbackQuery):
    await query.answer()
    index = int(query.data.replace("mkt_", ""))
    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        )).scalars().all()
    await show_market_card(query, cards, index)


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(query: CallbackQuery):
    await query.answer()
    card_id = int(query.data.replace("buy_", ""))
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        card = (await session.execute(select(Card).where(Card.id == card_id))).scalar_one_or_none()
        if not user or not card:
            await query.answer("❌ Не найдено", show_alert=True)
            return
        if user.balance < card.current_price:
            await query.answer(f"❌ Нужно {card.current_price} монет", show_alert=True)
            return
        user.balance -= card.current_price
        session.add(UserCard(user_id=user.id, card_id=card.id, acquired_price=card.current_price))
        await session.commit()
        name = card.name
    await query.answer(f"✅ Куплено: {name}", show_alert=True) 
