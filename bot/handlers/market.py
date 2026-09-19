"""Биржа: покупка карт у бота."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.constants import RARITY_EMOJI, RARITY_NAMES
from db.models import Card, User, UserCard
from db.session import AsyncSessionLocal
from services.economy import format_change, get_price_change

router = Router()


@router.callback_query(MainMenu.filter(F.action == "market"))
async def cb_market(query: CallbackQuery) -> None:
    """Открывает биржу."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        )).scalars().all()

    if not cards:
        await safe_render(query, "💹 <b>Биржа пуста</b>", get_back_menu())
        return

    await show_market_card(query, cards, 0)


async def show_market_card(query: CallbackQuery, cards: list, index: int) -> None:
    """Показывает карту на бирже."""
    card = cards[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")

    async with AsyncSessionLocal() as session:
        change = await get_price_change(session, card.id, hours=24)
    change_text = format_change(change)

    limit_text = ""
    if card.max_supply is not None:
        limit_text = f"\n📜 Тираж: <b>{card.issued}/{card.max_supply}</b>"

    text = (
        f"💹 <b>#{card.id} {card.name}</b>\n"
        f"Редкость: {RARITY_NAMES[card.rarity]} {emoji}\n"
        f"Команда: {card.team or '—'}\n"
        f"Цена: <b>{card.current_price}</b> {change_text}{limit_text}\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(cards)}</b>"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=f"mkt_{index - 1}")
    b.button(text=f"{index + 1}/{len(cards)}", callback_data="noop")
    if index < len(cards) - 1:
        b.button(text="➡️", callback_data=f"mkt_{index + 1}")
    b.button(text="💰 Купить", callback_data=f"buy_{card.id}")
    b.button(text="📊 Индекс", callback_data=f"idx_{card.id}")
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(3, 1, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(F.data.startswith("mkt_"))
async def cb_market_nav(query: CallbackQuery) -> None:
    """Навигация по бирже."""
    await safe_answer(query)
    index = int(query.data.replace("mkt_", ""))

    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card).where(Card.is_active == True).order_by(Card.current_price.desc()).limit(10)
        )).scalars().all()

    await show_market_card(query, cards, index)


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(query: CallbackQuery) -> None:
    """Покупка карты."""
    await safe_answer(query)
    card_id = int(query.data.replace("buy_", ""))

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        card = (await session.execute(
            select(Card).where(Card.id == card_id)
        )).scalar_one_or_none()

        if user is None or card is None:
            await safe_answer(query, "❌ Не найдено", show_alert=True)
            return

        if user.balance < card.current_price:
            await safe_answer(query, f"❌ Нужно {card.current_price} монет", show_alert=True)
            return

        user.balance -= card.current_price
        session.add(UserCard(
            user_id=user.id,
            card_id=card.id,
            acquired_price=card.current_price,
        ))
        await session.commit()
        card_name = card.name

    await safe_answer(query, f"✅ Куплено: {card_name}", show_alert=True) 
