from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from datetime import date, datetime

from bot.keyboards.main import MainMenu, get_main_menu
from bot.keyboards.cards import CardsMenu, CardsFilter, get_cards_menu, get_filter_menu, get_merge_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import RARITY_NAMES, RARITY_EMOJI
from db.session import AsyncSessionLocal
from db.models import User, Card, UserCard
from services.drop import drop_card
from services.merge import merge_cards
from services.economy import get_price_change, format_change

router = Router()


class TradeState(StatesGroup):
    waiting_username = State()


@router.callback_query(MainMenu.filter(F.action == "cards"))
async def cb_cards(query: CallbackQuery):
    await safe_answer(query)
    await safe_render(query, "🃏 <b>Карты</b>", get_cards_menu())


@router.callback_query(CardsMenu.filter(F.action == "back_to_cards"))
async def cb_cards_back(query: CallbackQuery):
    await safe_answer(query)
    await safe_render(query, "🃏 <b>Карты</b>", get_cards_menu())


@router.callback_query(CardsMenu.filter(F.action == "my"))
async def cb_my(query: CallbackQuery):
    await safe_answer(query)
    await safe_render(query, "🃏 <b>Фильтр коллекции</b>\n\nВыбери редкость:", get_filter_menu())


@router.callback_query(CardsFilter.filter())
async def cb_filter(query: CallbackQuery, callback_data: CardsFilter):
    await safe_answer(query)
    rarity = callback_data.rarity

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await safe_render(query, "❌ Сначала /start")
            return

        stmt = select(UserCard, Card).join(Card, UserCard.card_id == Card.id).where(UserCard.user_id == user.id)
        if rarity != "all":
            stmt = stmt.where(Card.rarity == rarity)
        rows = (await session.execute(stmt)).all()

    if not rows:
        await safe_render(query, f"🃏 <b>Нет карт</b> ({RARITY_NAMES.get(rarity, 'Все')})", get_filter_menu())
        return

    await show_card(query, rows, 0)


async def show_card(query: CallbackQuery, rows: list, index: int):
    uc, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    iw = " ⭐ IW" if uc.is_iw else ""

    async with AsyncSessionLocal() as session:
        change = await get_price_change(session, card.id, hours=24)
    change_text = format_change(change)

    limit_text = ""
    if card.max_supply:
        limit_text = f"\n📜 Тираж: <b>{card.issued}/{card.max_supply}</b>"
        if uc.serial_number:
            limit_text += f"\n🔢 Номер: <b>#{uc.serial_number}</b>"

    text = (
        f"🃏 <b>{card.name}</b>{iw}\n"
        f"Редкость: {RARITY_NAMES[card.rarity]} {emoji}\n"
        f"Команда: {card.team or '—'}\n"
        f"Цена: <b>{card.current_price}</b> {change_text}{limit_text}\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(rows)}</b>"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=f"crd_{index - 1}")
    b.button(text=f"{index + 1}/{len(rows)}", callback_data="noop")
    if index < len(rows) - 1:
        b.button(text="➡️", callback_data=f"crd_{index + 1}")
    b.button(text="📊 Индекс", callback_data=f"idx_{card.id}")
    b.button(text="🎁 Передать", callback_data=f"trd_{uc.id}")
    b.button(text="💰 Продать", callback_data=f"sll_{uc.id}")
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="my"))
    b.adjust(3, 2, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(F.data.startswith("crd_"))
async def cb_card_nav(query: CallbackQuery):
    await safe_answer(query)
    index = int(query.data.replace("crd_", ""))
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            return
        stmt = select(UserCard, Card).join(Card, UserCard.card_id == Card.id).where(UserCard.user_id == user.id)
        rows = (await session.execute(stmt)).all()
    if index < 0 or index >= len(rows):
        await safe_answer(query, "❌ Не найдено", show_alert=True)
        return
    await show_card(query, rows, index)


@router.callback_query(F.data.startswith("idx_"))
async def cb_index(query: CallbackQuery):
    await safe_answer(query)
    card_id = int(query.data.replace("idx_", ""))
    async with AsyncSessionLocal() as session:
        card = (await session.execute(select(Card).where(Card.id == card_id))).scalar_one_or_none()
        if not card:
            return
        changes = {}
        for label, hours in [("1 час", 1), ("6 часов", 6), ("24 часа", 24), ("7 дней", 168)]:
            changes[label] = await get_price_change(session, card.id, hours)

    text = f"📊 <b>{card.name}</b> — динамика\n\n"
    for label, change in changes.items():
        text += f"<b>{label}:</b> {format_change(change)}\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data="crd_0")
    await safe_render(query, text, b.as_markup())


@router.callback_query(F.data.startswith("trd_"))
async def cb_trade_start(query: CallbackQuery, state: FSMContext):
    await safe_answer(query)
    uc_id = int(query.data.replace("trd_", ""))
    await state.update_data(trade_uc_id=uc_id)
    await state.set_state(TradeState.waiting_username)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data="crd_0")
    await safe_render(query, "🎁 <b>Передача карты</b>\n\nВведи юз получателя (без @):", b.as_markup())


@router.message(TradeState.waiting_username)
async def cb_trade_confirm(message: Message, state: FSMContext):
    username = message.text.strip().lstrip("@").lower()
    data = await state.get_data()
    uc_id = data.get("trade_uc_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        sender = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        receiver = (await session.execute(select(User).where(User.username_normalized == username))).scalar_one_or_none()

        if not receiver:
            await message.answer("❌ Игрок не найден")
            return
        if sender.id == receiver.id:
            await message.answer("❌ Нельзя передать себе")
            return

        uc = (await session.execute(select(UserCard).where(UserCard.id == uc_id, UserCard.user_id == sender.id))).scalar_one_or_none()
        if not uc:
            await message.answer("❌ Карта не найдена")
            return

        card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
        uc.user_id = receiver.id
        uc.acquired_at = datetime.utcnow()
        await session.commit()

        card_name = card.name
        receiver_tg = receiver.telegram_id
        sender_name = sender.username

    await message.answer(f"✅ <b>Карта передана!</b>\n\nКому: @{username}\nКарта: {card_name}", parse_mode="HTML")
    try:
        await message.bot.send_message(receiver_tg, f"🎁 <b>Ты получил карту!</b>\n\nОт: @{sender_name}\nКарта: {card_name}", parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data.startswith("sll_"))
async def cb_sell(query: CallbackQuery):
    await safe_answer(query)
    uc_id = int(query.data.replace("sll_", ""))
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        uc = (await session.execute(select(UserCard).where(UserCard.id == uc_id, UserCard.user_id == user.id))).scalar_one_or_none()
        if not uc:
            return
        card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
        price = int(card.current_price * 0.97)
        user.balance += price
        await session.delete(uc)
        await session.commit()
        name = card.name
    await safe_answer(query, f"💰 Продано: {name} за {price}", show_alert=True)
    await cb_my(query)


@router.callback_query(CardsMenu.filter(F.action == "drop"))
async def cb_drop(query: CallbackQuery):
    await safe_answer(query)
    today = date.today()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await safe_render(query, "❌ Сначала /start")
            return

        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today
            await session.commit()

        if user.daily_attempts <= 0:
            await safe_render(query, "🎴 <b>Попытки закончились</b>\n\nВозвращайся завтра!", get_cards_menu())
            return

        card, is_iw = await drop_card(session)
        if not card:
            await safe_render(query, "❌ Нет карт в базе", get_cards_menu())
            return

        serial = None
        if card.max_supply:
            card.issued += 1
            serial = card.issued

        session.add(UserCard(user_id=user.id, card_id=card.id, is_iw=is_iw, acquired_price=card.current_price, serial_number=serial))
        user.daily_attempts -= 1
        await session.commit()
        remaining = user.daily_attempts

    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    iw_text = " ⭐ <b>INDY WINNER!</b>" if is_iw else ""
    limit_text = ""
    if card.max_supply:
        limit_text = f"\n📜 Тираж: <b>{card.issued}/{card.max_supply}</b>"
        if serial:
            limit_text += f"\n🔢 Твой номер: <b>#{serial}</b>"

    text = (
        f"🎴 <b>Дроп!</b>\n\n"
        f"{emoji} <b>{card.name}</b>{iw_text}\n"
        f"Редкость: {RARITY_NAMES[card.rarity]}\n"
        f"Цена: {card.current_price}{limit_text}\n\n"
        f"Осталось: <b>{remaining}</b>"
    )

    b = InlineKeyboardBuilder()
    b.button(text="🎴 Ещё раз", callback_data=CardsMenu(action="drop"))
    b.button(text="🃏 Коллекция", callback_data=CardsMenu(action="my"))
    b.button(text="🔙 Меню", callback_data=MainMenu(action="back"))
    b.adjust(2, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(CardsMenu.filter(F.action == "merge"))
async def cb_merge_menu(query: CallbackQuery):
    await safe_answer(query)
    await safe_render(
        query,
        "🔀 <b>Слияние карт</b>\n\n3 карты → 1 новая\nШанс: <b>70%</b>\nLegendary → Limited: <b>20%</b>",
        get_merge_menu()
    )


@router.callback_query(F.data.startswith("mg_"))
async def cb_merge(query: CallbackQuery):
    await safe_answer(query)
    rarity = query.data.replace("mg_", "")

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            return
        result = await merge_cards(session, user.id, rarity)

    if not result["ok"]:
        await safe_answer(query, result["reason"], show_alert=True)
        return

    if result["result"] == "burn":
        await safe_render(query, "❌ <b>Фейл!</b>\n\nКарты сгорели.", get_merge_menu())
    else:
        await safe_render(query, f"✅ <b>Успех!</b>\n\nПолучена: {RARITY_NAMES[result['result']]}\n{result['card_name']}", get_merge_menu())


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery):
    await safe_answer(query)
