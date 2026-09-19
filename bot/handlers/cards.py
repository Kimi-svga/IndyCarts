"""Обработчики карт: коллекция, дроп, трейды, продажа, слияние."""

from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.cards import (
    CardsFilter, CardsMenu, get_cards_menu, get_filter_menu, get_merge_menu,
)
from bot.keyboards.main import MainMenu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import MARKET_FEE, RARITY_EMOJI, RARITY_NAMES
from db.models import Card, User, UserCard
from db.session import AsyncSessionLocal
from services.drop import Drop
from services.economy import format_change, get_price_change
from services.merge import merge_cards

router = Router()


class TradeState(StatesGroup):
    """Ожидание юза при трейде."""
    waiting_username = State()


# ─────────────────────────────────────────────
# МЕНЮ КАРТ
# ─────────────────────────────────────────────

@router.callback_query(MainMenu.filter(F.action == "cards"))
async def cb_cards(query: CallbackQuery) -> None:
    """Открывает меню карт."""
    await safe_answer(query)
    await safe_render(query, "🃏 <b>Карты</b>", get_cards_menu())


@router.callback_query(CardsMenu.filter(F.action == "back_to_cards"))
async def cb_cards_back(query: CallbackQuery) -> None:
    """Возврат из фильтров/слияния."""
    await safe_answer(query)
    await safe_render(query, "🃏 <b>Карты</b>", get_cards_menu())


# ─────────────────────────────────────────────
# КОЛЛЕКЦИЯ
# ─────────────────────────────────────────────

@router.callback_query(CardsMenu.filter(F.action == "my"))
async def cb_my(query: CallbackQuery) -> None:
    """Открывает фильтр коллекции."""
    await safe_answer(query)
    await safe_render(
        query,
        "🃏 <b>Фильтр коллекции</b>\n\nВыбери редкость:",
        get_filter_menu(),
    )


@router.callback_query(CardsFilter.filter())
async def cb_filter(query: CallbackQuery, callback_data: CardsFilter) -> None:
    """Показывает карты игрока выбранной редкости."""
    await safe_answer(query)
    rarity = callback_data.rarity

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )
        if rarity != "all":
            stmt = stmt.where(Card.rarity == rarity)

        rows = (await session.execute(stmt)).all()

    if not rows:
        await safe_render(
            query,
            f"🃏 <b>Нет карт</b> ({RARITY_NAMES.get(rarity, 'Все')})",
            get_filter_menu(),
        )
        return

    await show_card(query, rows, 0)


async def show_card(query: CallbackQuery, rows: list, index: int) -> None:
    """Показывает карту с навигацией."""
    user_card, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    iw = " ⭐ IW" if user_card.is_iw else ""

    async with AsyncSessionLocal() as session:
        change = await get_price_change(session, card.id, hours=24)
    change_text = format_change(change)

    limit_text = ""
    if card.max_supply is not None:
        limit_text = f"\n📜 Тираж: <b>{card.issued}/{card.max_supply}</b>"
        if user_card.serial_number is not None:
            limit_text += f"\n🔢 Номер: <b>#{user_card.serial_number}</b>"

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
    b.button(text="🎁 Передать", callback_data=f"trd_{user_card.id}")
    b.button(text="💰 Продать", callback_data=f"sll_{user_card.id}")
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="my"))
    b.adjust(3, 2, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(F.data.startswith("crd_"))
async def cb_card_nav(query: CallbackQuery) -> None:
    """Навигация по карусели."""
    await safe_answer(query)
    index = int(query.data.replace("crd_", ""))

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )
        rows = (await session.execute(stmt)).all()

    if index < 0 or index >= len(rows):
        await safe_answer(query, "❌ Не найдено", show_alert=True)
        return

    await show_card(query, rows, index)


# ─────────────────────────────────────────────
# ИНДЕКС ЦЕНЫ
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("idx_"))
async def cb_index(query: CallbackQuery) -> None:
    """Показывает динамику цены за 1ч, 6ч, 24ч, 7д."""
    await safe_answer(query)
    card_id = int(query.data.replace("idx_", ""))

    async with AsyncSessionLocal() as session:
        card = (await session.execute(
            select(Card).where(Card.id == card_id)
        )).scalar_one_or_none()

        if card is None:
            await safe_answer(query, "❌ Карта не найдена", show_alert=True)
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


# ─────────────────────────────────────────────
# ТРЕЙД
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("trd_"))
async def cb_trade_start(query: CallbackQuery, state: FSMContext) -> None:
    """Начинает трейд: запрашивает юз."""
    await safe_answer(query)
    user_card_id = int(query.data.replace("trd_", ""))
    await state.update_data(trade_uc_id=user_card_id)
    await state.set_state(TradeState.waiting_username)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data="crd_0")
    await safe_render(
        query,
        "🎁 <b>Передача карты</b>\n\nВведи юз получателя (без @):",
        b.as_markup(),
    )


@router.message(TradeState.waiting_username)
async def cb_trade_confirm(message: Message, state: FSMContext) -> None:
    """Обрабатывает ввод юза и передаёт карту."""
    username = message.text.strip().lstrip("@").lower()
    data = await state.get_data()
    user_card_id = data.get("trade_uc_id")
    await state.clear()

    if not username:
        await message.answer("❌ Пустой юз")
        return

    async with AsyncSessionLocal() as session:
        sender = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        receiver = (await session.execute(
            select(User).where(User.username_normalized == username)
        )).scalar_one_or_none()

        if sender is None:
            await message.answer("❌ Сначала /start")
            return
        if receiver is None:
            await message.answer("❌ Игрок не найден")
            return
        if sender.id == receiver.id:
            await message.answer("❌ Нельзя передать себе")
            return

        user_card = (await session.execute(
            select(UserCard).where(
                UserCard.id == user_card_id,
                UserCard.user_id == sender.id,
            )
        )).scalar_one_or_none()

        if user_card is None:
            await message.answer("❌ Карта не найдена")
            return

        card = (await session.execute(
            select(Card).where(Card.id == user_card.card_id)
        )).scalar_one_or_none()

        user_card.user_id = receiver.id
        user_card.acquired_at = datetime.utcnow()
        await session.commit()

        card_name = card.name
        receiver_tg = receiver.telegram_id
        sender_name = sender.username

    await message.answer(
        f"✅ <b>Карта передана!</b>\n\n"
        f"Кому: @{username}\n"
        f"Карта: {card_name}",
        parse_mode="HTML",
    )

    try:
        await message.bot.send_message(
            receiver_tg,
            f"🎁 <b>Ты получил карту!</b>\n\n"
            f"От: @{sender_name}\n"
            f"Карта: {card_name}",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
# ПРОДАЖА (без кулдауна)
# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("sll_"))
async def cb_sell(query: CallbackQuery) -> None:
    """Продаёт карту боту с комиссией MARKET_FEE. Без кулдауна."""
    await safe_answer(query)
    user_card_id = int(query.data.replace("sll_", ""))

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        user_card = (await session.execute(
            select(UserCard).where(
                UserCard.id == user_card_id,
                UserCard.user_id == user.id,
            )
        )).scalar_one_or_none()

        if user_card is None:
            await safe_answer(query, "❌ Карта не найдена", show_alert=True)
            return

        card = (await session.execute(
            select(Card).where(Card.id == user_card.card_id)
        )).scalar_one_or_none()

        price = int(card.current_price * (1 - MARKET_FEE))
        user.balance += price
        await session.delete(user_card)
        await session.commit()
        card_name = card.name

    await safe_answer(query, f"💰 Продано: {card_name} за {price}", show_alert=True)
    await cb_my(query)


# ─────────────────────────────────────────────
# ДРОП (без кулдауна)
# ─────────────────────────────────────────────

@router.callback_query(CardsMenu.filter(F.action == "drop"))
async def cb_drop(query: CallbackQuery) -> None:
    """Дроп карты. Без кулдауна — защита через лимит попыток и комиссию."""
    await safe_answer(query)
    today = date.today()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        # Сброс попыток в полночь
        if user.last_attempt_date != today:
            user.daily_attempts = settings.DAILY_ATTEMPTS
            user.last_attempt_date = today
            await session.commit()

        if user.daily_attempts <= 0:
            await safe_render(
                query,
                "🎴 <b>Попытки закончились</b>\n\nВозвращайся завтра!",
                get_cards_menu(),
            )
            return

        card, is_iw = await Drop.drop_card(session)
        if card is None:
            await safe_render(query, "❌ Нет карт в базе", get_cards_menu())
            return

        serial = None
        if card.max_supply is not None:
            card.issued += 1
            serial = card.issued

        session.add(UserCard(
            user_id=user.id,
            card_id=card.id,
            is_iw=is_iw,
            acquired_price=card.current_price,
            serial_number=serial,
        ))
        user.daily_attempts -= 1
        await session.commit()

        remaining = user.daily_attempts
        card_issued = card.issued
        card_max_supply = card.max_supply
        card_name = card.name
        card_rarity = card.rarity
        card_price = card.current_price
        card_image = card.image_file_id

    emoji = RARITY_EMOJI.get(card_rarity, "⚪")
    iw_text = " ⭐ <b>INDY WINNER!</b>" if is_iw else ""
    limit_text = ""
    if card_max_supply is not None:
        limit_text = f"\n📜 Тираж: <b>{card_issued}/{card_max_supply}</b>"
        if serial is not None:
            limit_text += f"\n🔢 Твой номер: <b>#{serial}</b>"

    text = (
        f"🎴 <b>Дроп!</b>\n\n"
        f"{emoji} <b>{card_name}</b>{iw_text}\n"
        f"Редкость: {RARITY_NAMES[card_rarity]}\n"
        f"Цена: {card_price}{limit_text}\n\n"
        f"Осталось: <b>{remaining}</b>"
    )

    b = InlineKeyboardBuilder()
    b.button(text="🎴 Ещё раз", callback_data=CardsMenu(action="drop"))
    b.button(text="🃏 Коллекция", callback_data=CardsMenu(action="my"))
    b.button(text="🔙 Меню", callback_data=MainMenu(action="back"))
    b.adjust(2, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card_image)


# ─────────────────────────────────────────────
# СЛИЯНИЕ
# ─────────────────────────────────────────────

@router.callback_query(CardsMenu.filter(F.action == "merge"))
async def cb_merge_menu(query: CallbackQuery) -> None:
    """Открывает меню слияния."""
    await safe_answer(query)
    await safe_render(
        query,
        "🔀 <b>Слияние карт</b>\n\n"
        "3 карты → 1 новая\n"
        "Шанс успеха: <b>70%</b>\n"
        "Legendary → Limited: <b>20%</b>",
        get_merge_menu(),
    )


@router.callback_query(F.data.startswith("mg_"))
async def cb_merge(query: CallbackQuery) -> None:
    """Обрабатывает слияние."""
    await safe_answer(query)
    rarity = query.data.replace("mg_", "")

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        result = await merge_cards(session, user.id, rarity)

    if not result.ok:
        await safe_answer(query, result.reason or "❌ Ошибка", show_alert=True)
        return

    if result.result == "burn":
        await safe_render(
            query,
            "❌ <b>Фейл!</b>\n\nКарты сгорели.",
            get_merge_menu(),
        )
    else:
        await safe_render(
            query,
            f"✅ <b>Успех!</b>\n\n"
            f"Получена: {RARITY_NAMES[result.result]}\n"
            f"{result.card_name}",
            get_merge_menu(),
        )


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    """Пустой колбэк."""
    await safe_answer(query) 
