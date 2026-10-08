"""Редактор карт: всё кнопками."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import delete, func, select

from bot.keyboards.admin_cards import (
    ACard, get_card_editor, get_card_list_nav, get_collection_menu,
    get_delete_confirm, get_price_menu, get_rarity_menu, get_team_menu,
    get_year_menu,
)
from bot.keyboards.main import get_back_menu
from bot.utils.decorators import check_role
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    CEILING_MULTIPLIER, FLOOR_MULTIPLIER,
    RARITY_EMOJI, RARITY_NAMES,
)
from core.logger import setup_logger
from db.models import Card, Collection, UserCard
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()

PER_PAGE = settings.CARD_LIST_PER_PAGE


class ACardState(StatesGroup):
    waiting_name = State()
    waiting_image = State()
    waiting_team = State()
    waiting_year = State()
    waiting_price = State()
    waiting_weight = State()
    waiting_supply = State()
    waiting_search = State()
    waiting_collection_name = State()


# ═════════════════════════════════════════════
# СПИСОК
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "list"))
async def cb_list(query: CallbackQuery, callback_data: ACard) -> None:
    if not await check_role(query.from_user.id, "admin"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)
    await _show_list(query, callback_data.index)


async def _show_list(query: CallbackQuery, index: int) -> None:
    async with AsyncSessionLocal() as session:
        total = (await session.execute(select(func.count(Card.id)))).scalar() or 0
        cards = (await session.execute(
            select(Card)
            .order_by(Card.id.desc())
            .offset(index * PER_PAGE)
            .limit(PER_PAGE)
        )).scalars().all()

    if not cards:
        await safe_render(query, "📭 Карт нет", get_back_menu())
        return

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)

    text = f"✏️ <b>Редактор карт</b>\n\nВсего: {total}\nСтраница {index + 1}/{total_pages}"

    b = InlineKeyboardBuilder()
    for c in cards:
        emoji = RARITY_EMOJI.get(c.rarity, "⚪")
        status = "✅" if c.in_drop else "🚫"
        b.button(
            text=f"{status} {emoji} #{c.id} {c.name[:22]}",
            callback_data=ACard(action="view", card_id=c.id).pack(),
        )
    b.adjust(1)
    b.attach(get_card_list_nav(index, total_pages))

    await safe_render(query, text, b.as_markup())


# ═════════════════════════════════════════════
# КАРТОЧКА
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: ACard) -> None:
    if not await check_role(query.from_user.id, "admin"):
        return
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card is None:
            await safe_answer(query, "❌ Карта не найдена", show_alert=True)
            return

        collection_name = "—"
        if card.collection_id:
            col = await session.get(Collection, card.collection_id)
            if col:
                collection_name = f"{col.emoji or '📁'} {col.name}"

        emoji = RARITY_EMOJI.get(card.rarity, "⚪")
        text = (
            f"✏️ <b>Редактор · #{card.id}</b>\n\n"
            f"📝 <b>{card.name}</b>\n"
            f"Редкость: {emoji} {RARITY_NAMES.get(card.rarity, card.rarity)}\n"
            f"Команда: {card.team or '—'}\n"
            f"Год: {card.year or '—'}\n"
            f"Цена: <b>{card.current_price:,}</b>\n"
            f"Вес дропа: {card.drop_weight}\n"
            f"Тираж: {card.max_supply or '∞'} ({card.issued})\n"
            f"Коллекция: {collection_name}\n"
            f"Статус: {'✅ в дропе' if card.in_drop else '🚫 вне дропа'}"
        )
        image = card.image_file_id
        in_drop = card.in_drop

    await safe_render(
        query, text,
        get_card_editor(callback_data.card_id, in_drop=in_drop),
        photo_file_id=image,
    )


# ═════════════════════════════════════════════
# НАЗВАНИЕ
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_name"))
async def cb_edit_name(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_name)
    await safe_render(query, "📝 Введи новое название:", get_back_menu())


@router.message(ACardState.waiting_name)
async def handle_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()[:128]
    if len(name) < 2:
        await message.answer("❌ Минимум 2 символа")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.name = name
            await session.commit()

    await message.answer("✅ Название обновлено")


# ═════════════════════════════════════════════
# КАРТИНКА
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_image"))
async def cb_edit_image(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_image)
    await safe_render(query, "🖼 Отправь фото или <code>skip</code>", get_back_menu())


@router.message(ACardState.waiting_image, F.photo)
async def handle_image_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.image_file_id = message.photo[-1].file_id
            await session.commit()

    await message.answer("✅ Картинка обновлена")


@router.message(ACardState.waiting_image, F.text == "skip")
async def handle_image_skip(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.image_file_id = None
            await session.commit()

    await message.answer("✅ Картинка удалена")


# ═════════════════════════════════════════════
# РЕДКОСТЬ
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_rarity"))
async def cb_edit_rarity(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "🎨 Выбери редкость",
        get_rarity_menu(callback_data.card_id),
    )


@router.callback_query(ACard.filter(F.action == "set_rarity"))
async def cb_set_rarity(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            card.rarity = callback_data.value
            await session.commit()

    await safe_answer(query, "✅ Редкость обновлена")
    await cb_view(query, ACard(action="view", card_id=callback_data.card_id))


# ═════════════════════════════════════════════
# КОМАНДА
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_team"))
async def cb_edit_team(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    teams = await _get_teams()
    await safe_render(
        query,
        f"🏁 Выбери команду\n\nВсего: {len(teams)}",
        get_team_menu(callback_data.card_id, teams, 0),
    )


@router.callback_query(ACard.filter(F.action == "team_page"))
async def cb_team_page(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    teams = await _get_teams()
    await safe_render(
        query,
        f"🏁 Выбери команду\n\nВсего: {len(teams)}",
        get_team_menu(callback_data.card_id, teams, callback_data.index),
    )


@router.callback_query(ACard.filter(F.action == "set_team"))
async def cb_set_team(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            card.team = callback_data.value
            await session.commit()

    await safe_answer(query, "✅ Команда обновлена")
    await cb_view(query, ACard(action="view", card_id=callback_data.card_id))


@router.callback_query(ACard.filter(F.action == "set_team_manual"))
async def cb_set_team_manual(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_team)
    await safe_render(query, "✏️ Введи название команды:", get_back_menu())


@router.message(ACardState.waiting_team)
async def handle_team(message: Message, state: FSMContext) -> None:
    team = message.text.strip()[:64]
    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.team = team
            await session.commit()

    await message.answer("✅ Команда обновлена")


async def _get_teams() -> list[str]:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(Card.team)
            .where(Card.team.is_not(None), Card.team != "")
            .distinct()
            .order_by(Card.team)
        )).scalars().all()
    return [r for r in rows if r]


# ═════════════════════════════════════════════
# ГОД
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_year"))
async def cb_edit_year(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    years = await _get_years()
    await safe_render(
        query,
        f"📅 Выбери год\n\nВсего: {len(years)}",
        get_year_menu(callback_data.card_id, years, 0),
    )


@router.callback_query(ACard.filter(F.action == "year_page"))
async def cb_year_page(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    years = await _get_years()
    await safe_render(
        query,
        f"📅 Выбери год\n\nВсего: {len(years)}",
        get_year_menu(callback_data.card_id, years, callback_data.index),
    )


@router.callback_query(ACard.filter(F.action == "set_year"))
async def cb_set_year(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            card.year = int(callback_data.value)
            await session.commit()

    await safe_answer(query, "✅ Год обновлён")
    await cb_view(query, ACard(action="view", card_id=callback_data.card_id))


@router.callback_query(ACard.filter(F.action == "set_year_manual"))
async def cb_set_year_manual(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_year)
    await safe_render(query, "✏️ Введи год (1900–2100):", get_back_menu())


@router.message(ACardState.waiting_year)
async def handle_year(message: Message, state: FSMContext) -> None:
    try:
        year = int(message.text.strip())
        if year < 1900 or year > 2100:
            raise ValueError
    except ValueError:
        await message.answer("❌ Год 1900–2100")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.year = year
            await session.commit()

    await message.answer("✅ Год обновлён")


async def _get_years() -> list[int]:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(Card.year)
            .where(Card.year.is_not(None))
            .distinct()
            .order_by(Card.year.desc())
            .limit(30)
        )).scalars().all()
    return [r for r in rows if r]


# ═════════════════════════════════════════════
# ЦЕНА
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_price"))
async def cb_edit_price(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card is None:
            return
        current = card.current_price

    await safe_render(
        query,
        f"💰 <b>Цена</b>\n\nТекущая: <b>{current:,}</b>\n\nВыбери:",
        get_price_menu(callback_data.card_id),
    )


@router.callback_query(ACard.filter(F.action == "price_delta"))
async def cb_price_delta(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    delta = int(callback_data.value)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            new_price = max(1, card.base_price + delta)
            card.base_price = new_price
            card.current_price = new_price
            card.floor_price = int(new_price * FLOOR_MULTIPLIER)
            card.ceiling_price = int(new_price * CEILING_MULTIPLIER)
            await session.commit()
            new = new_price
        else:
            new = 0

    await safe_answer(query, f"✅ Цена: {new:,}", show_alert=False)
    await safe_render(
        query,
        f"💰 <b>Цена</b>\n\nТекущая: <b>{new:,}</b>",
        get_price_menu(callback_data.card_id),
    )


@router.callback_query(ACard.filter(F.action == "set_price_manual"))
async def cb_price_manual(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_price)
    await safe_render(query, "✏️ Введи новую цену:", get_back_menu())


@router.message(ACardState.waiting_price)
async def handle_price(message: Message, state: FSMContext) -> None:
    try:
        price = int(message.text.strip())
        if price < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Число > 0")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.base_price = price
            card.current_price = price
            card.floor_price = int(price * FLOOR_MULTIPLIER)
            card.ceiling_price = int(price * CEILING_MULTIPLIER)
            await session.commit()

    await message.answer(f"✅ Цена: {price:,}")


# ═════════════════════════════════════════════
# ВЕС / ТИРАЖ
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_weight"))
async def cb_edit_weight(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_weight)
    await safe_render(query, "⚖️ Введи вес дропа (1–1000):", get_back_menu())


@router.message(ACardState.waiting_weight)
async def handle_weight(message: Message, state: FSMContext) -> None:
    try:
        w = int(message.text.strip())
        if w < 1 or w > 1000:
            raise ValueError
    except ValueError:
        await message.answer("❌ 1–1000")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.drop_weight = w
            await session.commit()

    await message.answer(f"✅ Вес: {w}")


@router.callback_query(ACard.filter(F.action == "edit_supply"))
async def cb_edit_supply(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_supply)
    await safe_render(query, "📜 Введи тираж (0 = без лимита):", get_back_menu())


@router.message(ACardState.waiting_supply)
async def handle_supply(message: Message, state: FSMContext) -> None:
    try:
        s = int(message.text.strip())
        if s < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Число ≥ 0")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if card:
            card.max_supply = s if s > 0 else None
            await session.commit()

    await message.answer("✅ Тираж обновлён")


# ═════════════════════════════════════════════
# КОЛЛЕКЦИЯ
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "edit_collection"))
async def cb_edit_collection(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    collections = await _get_collections()
    await safe_render(
        query,
        f"📁 Выбери коллекцию\n\nВсего: {len(collections)}",
        get_collection_menu(callback_data.card_id, collections, 0),
    )


@router.callback_query(ACard.filter(F.action == "col_page"))
async def cb_col_page(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    collections = await _get_collections()
    await safe_render(
        query,
        f"📁 Выбери коллекцию\n\nВсего: {len(collections)}",
        get_collection_menu(callback_data.card_id, collections, callback_data.index),
    )


@router.callback_query(ACard.filter(F.action == "set_collection"))
async def cb_set_collection(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    cid = int(callback_data.value) if callback_data.value != "0" else None

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            card.collection_id = cid
            await session.commit()

    await safe_answer(query, "✅ Коллекция обновлена")
    await cb_view(query, ACard(action="view", card_id=callback_data.card_id))


@router.callback_query(ACard.filter(F.action == "create_collection"))
async def cb_create_collection(query: CallbackQuery, callback_data: ACard, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(card_id=callback_data.card_id)
    await state.set_state(ACardState.waiting_collection_name)
    await safe_render(query, "➕ Введи название коллекции:", get_back_menu())


@router.message(ACardState.waiting_collection_name)
async def handle_collection_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()[:64]
    if len(name) < 2:
        await message.answer("❌ Минимум 2 символа")
        return

    data = await state.get_data()
    card_id = data.get("card_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(Collection).where(Collection.name == name)
        )).scalar_one_or_none()

        if existing is None:
            existing = Collection(name=name)
            session.add(existing)
            await session.flush()

        card = await session.get(Card, card_id)
        if card:
            card.collection_id = existing.id

        await session.commit()

    await message.answer(f"✅ Коллекция «{name}» создана и привязана")


async def _get_collections() -> list:
    async with AsyncSessionLocal() as session:
        return (await session.execute(
            select(Collection).order_by(Collection.name).limit(50)
        )).scalars().all()


# ═════════════════════════════════════════════
# ДРОП / УДАЛЕНИЕ
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "toggle_drop"))
async def cb_toggle_drop(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            card.in_drop = not card.in_drop
            await session.commit()
            new_state = card.in_drop
        else:
            new_state = True

    text = "✅ Карта возвращена в дроп" if new_state else "🚫 Карта убрана из дропа"
    await safe_answer(query, text, show_alert=False)
    await cb_view(query, ACard(action="view", card_id=callback_data.card_id))


@router.callback_query(ACard.filter(F.action == "delete"))
async def cb_delete(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "❌ <b>Удалить карту?</b>\n\n"
        "Это действие нельзя отменить. "
        "Все копии у игроков будут удалены.",
        get_delete_confirm(callback_data.card_id),
    )


@router.callback_query(ACard.filter(F.action == "delete_confirm"))
async def cb_delete_confirm(query: CallbackQuery, callback_data: ACard) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, callback_data.card_id)
        if card:
            name = card.name
            await session.execute(
                delete(UserCard).where(UserCard.card_id == card.id)
            )
            await session.delete(card)
            await session.commit()
        else:
            name = "?"

    await safe_render(query, f"🗑 Удалено: {name}", get_back_menu())


# ═════════════════════════════════════════════
# ПОИСК
# ═════════════════════════════════════════════

@router.callback_query(ACard.filter(F.action == "search"))
async def cb_search(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(ACardState.waiting_search)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data=ACard(action="list", index=0).pack())
    b.adjust(1)

    await safe_render(query, "🔍 Введи имя карты:", b.as_markup())


@router.message(ACardState.waiting_search)
async def handle_search(message: Message, state: FSMContext) -> None:
    q = message.text.strip()
    await state.clear()

    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card)
            .where(Card.name.ilike(f"%{q}%"))
            .order_by(Card.id.desc())
            .limit(settings.CARD_SEARCH_LIMIT)
        )).scalars().all()

    if not cards:
        await message.answer(f"❌ Ничего по запросу «{q}»")
        return

    b = InlineKeyboardBuilder()
    for c in cards:
        emoji = RARITY_EMOJI.get(c.rarity, "⚪")
        b.button(
            text=f"{emoji} #{c.id} {c.name[:24]}",
            callback_data=ACard(action="view", card_id=c.id).pack(),
        )
    b.button(text="🔙 В админку", callback_data="menu:admin_panel")
    b.adjust(1)

    await message.answer(
        f"🔍 Найдено: {len(cards)}",
        reply_markup=b.as_markup(),
    )


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query)
