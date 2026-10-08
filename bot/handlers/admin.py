"""Админ: карты, промокоды, рассылка, статистика, импорт, команды."""

import asyncio
import json

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from bot.keyboards.admin import AdminMenu, get_admin_menu
from bot.keyboards.admin_cards import ACard
from bot.keyboards.main import get_back_menu
from bot.utils.decorators import require_admin
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    CEILING_MULTIPLIER, FLOOR_MULTIPLIER,
    RARITIES, RARITY_EMOJI, RARITY_NAMES,
)
from db.models import Card, PromoCode, PvpReward, Reward, User
from db.session import AsyncSessionLocal

router = Router()


class AddCard(StatesGroup):
    name = State()
    rarity = State()
    team = State()
    year = State()
    price = State()
    weight = State()
    supply = State()
    image = State()


class AddPromo(StatesGroup):
    code = State()
    money = State()
    attempts = State()
    max_acts = State()
    card = State()


class Broadcast(StatesGroup):
    content = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    uid = message.from_user.id
    is_allowed = uid in settings.OWNER_IDS or uid in settings.ADMIN_IDS

    if not is_allowed:
        from db.models import AdminRole
        async with AsyncSessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == uid)
            )).scalar_one_or_none()
            if user is not None:
                role = (await session.execute(
                    select(AdminRole).where(AdminRole.user_id == user.id)
                )).scalar_one_or_none()
                if role is not None:
                    is_allowed = True

    if not is_allowed:
        return

    await message.answer(
        "👑 <b>Панель P4/9</b>",
        reply_markup=get_admin_menu(),
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# РЕДАКТОР КАРТ — РЕДИРЕКТ В admin_cards
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "edit_cards"))
@require_admin
async def cb_edit_cards_redirect(query: CallbackQuery) -> None:
    """Старая кнопка — редирект в новый редактор."""
    await safe_answer(query)
    from bot.handlers.admin_cards import cb_list
    await cb_list(query, ACard(action="list", index=0))


# ─────────────────────────────────────────────
# СОЗДАНИЕ КАРТЫ (FSM — оставлено)
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "add_card"))
@require_admin
async def cb_add_card(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(AddCard.name)
    await safe_render(query, "➕ <b>Новая карта</b>\n\nШаг 1/8: Имя пилота")


@router.message(AddCard.name)
async def ac_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCard.rarity)

    b = InlineKeyboardBuilder()
    for r in RARITIES:
        b.button(text=RARITY_NAMES[r], callback_data=f"ar_{r}")
    b.adjust(2)

    await message.answer("Шаг 2/8: Редкость", reply_markup=b.as_markup())


@router.callback_query(F.data.startswith("ar_"))
async def ac_rarity(query: CallbackQuery, state: FSMContext) -> None:
    rarity = query.data.replace("ar_", "")
    await state.update_data(rarity=rarity)
    await state.set_state(AddCard.team)
    await safe_answer(query)
    await query.message.edit_text("Шаг 3/8: Команда")


@router.message(AddCard.team)
async def ac_team(message: Message, state: FSMContext) -> None:
    await state.update_data(team=message.text.strip())
    await state.set_state(AddCard.year)
    await message.answer("Шаг 4/8: Год")


@router.message(AddCard.year)
async def ac_year(message: Message, state: FSMContext) -> None:
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Год — число")
        return
    await state.update_data(year=year)
    await state.set_state(AddCard.price)
    await message.answer("Шаг 5/8: Базовая цена")


@router.message(AddCard.price)
async def ac_price(message: Message, state: FSMContext) -> None:
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Цена — число")
        return
    await state.update_data(price=price)
    await state.set_state(AddCard.weight)
    await message.answer("Шаг 6/8: Вес дропа (100 = стандарт)")


@router.message(AddCard.weight)
async def ac_weight(message: Message, state: FSMContext) -> None:
    try:
        weight = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Вес — число")
        return
    await state.update_data(weight=weight)
    await state.set_state(AddCard.supply)
    await message.answer("Шаг 7/8: Лимит тиража (0 = без лимита)")


@router.message(AddCard.supply)
async def ac_supply(message: Message, state: FSMContext) -> None:
    try:
        supply = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(supply=supply if supply > 0 else None)
    await state.set_state(AddCard.image)
    await message.answer("Шаг 8/8: Отправь фото или <code>skip</code>", parse_mode="HTML")


@router.message(AddCard.image, F.photo)
async def ac_image(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        session.add(Card(
            name=data["name"], rarity=data["rarity"],
            team=data["team"], year=data["year"],
            base_price=data["price"], current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            drop_weight=data["weight"], max_supply=data.get("supply"),
            image_file_id=file_id, created_by=message.from_user.id,
        ))
        await session.commit()

    supply_text = f"\n📜 Тираж: {data['supply']}" if data.get("supply") else "\n📜 Без лимита"
    await message.answer(f"✅ Карта добавлена: {data['name']}{supply_text}")


@router.message(AddCard.image, F.text == "skip")
async def ac_skip(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        session.add(Card(
            name=data["name"], rarity=data["rarity"],
            team=data["team"], year=data["year"],
            base_price=data["price"], current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            drop_weight=data["weight"], max_supply=data.get("supply"),
            created_by=message.from_user.id,
        ))
        await session.commit()

    await message.answer(f"✅ Карта добавлена: {data['name']}")


# ─────────────────────────────────────────────
# МАССОВАЯ ЗАГРУЗКА
# ─────────────────────────────────────────────

@router.message(Command("importcards"))
async def cmd_import(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS and message.from_user.id not in settings.ADMIN_IDS:
        return
    await message.answer("📦 Отправь JSON-файл с картами")


@router.message(F.document)
async def handle_import(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS and message.from_user.id not in settings.ADMIN_IDS:
        return

    if not message.document or not message.document.file_name:
        return
    if not message.document.file_name.endswith(".json"):
        return

    file = await message.bot.get_file(message.document.file_id)
    content = await message.bot.download_file(file.file_path)
    data = json.loads(content.read().decode("utf-8"))

    async with AsyncSessionLocal() as session:
        count = 0
        for item in data:
            base = item.get("base_price", 100)
            session.add(Card(
                name=item["name"], rarity=item["rarity"],
                team=item.get("team"), year=item.get("year"),
                base_price=base, current_price=base,
                floor_price=int(base * FLOOR_MULTIPLIER),
                ceiling_price=int(base * CEILING_MULTIPLIER),
                drop_weight=item.get("drop_weight", 100),
                max_supply=item.get("max_supply"),
                image_file_id=item.get("image_file_id"),
                created_by=message.from_user.id,
            ))
            count += 1
        await session.commit()

    await message.answer(f"✅ Загружено: {count} карт")


# ─────────────────────────────────────────────
# ПРОМОКОДЫ
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "add_promo"))
@require_admin
async def cb_add_promo(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(AddPromo.code)
    await safe_render(query, "🎁 Шаг 1/5: Код промокода")


@router.message(AddPromo.code)
async def ap_code(message: Message, state: FSMContext) -> None:
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AddPromo.money)
    await message.answer("Шаг 2/5: Монеты")


@router.message(AddPromo.money)
async def ap_money(message: Message, state: FSMContext) -> None:
    try:
        money = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(money=money)
    await state.set_state(AddPromo.attempts)
    await message.answer("Шаг 3/5: Попытки")


@router.message(AddPromo.attempts)
async def ap_attempts(message: Message, state: FSMContext) -> None:
    try:
        attempts = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(attempts=attempts)
    await state.set_state(AddPromo.max_acts)
    await message.answer("Шаг 4/5: Максимум активаций (0 = без лимита)")


@router.message(AddPromo.max_acts)
async def ap_max_acts(message: Message, state: FSMContext) -> None:
    try:
        max_acts = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(max_acts=max_acts if max_acts > 0 else None)
    await state.set_state(AddPromo.card)
    await message.answer("Шаг 5/5: ID карты (0 = без карты)")


@router.message(AddPromo.card)
async def ap_card(message: Message, state: FSMContext) -> None:
    try:
        card_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return

    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        session.add(PromoCode(
            code=data["code"],
            reward_money=data["money"],
            reward_attempts=data["attempts"],
            reward_card_id=card_id if card_id > 0 else None,
            max_activations=data.get("max_acts"),
        ))
        await session.commit()

    card_text = f"\n🎴 + карта #{card_id}" if card_id > 0 else ""
    limit_text = f"\n🔢 Лимит: {data['max_acts']}" if data.get("max_acts") else "\n🔢 Без лимита"

    await message.answer(
        f"✅ Промокод <code>{data['code']}</code> создан\n"
        f"💰 +{data['money']} монет\n"
        f"🎴 +{data['attempts']} попыток"
        f"{card_text}{limit_text}",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# РАССЫЛКА
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "broadcast"))
@require_admin
async def cb_broadcast(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(Broadcast.content)
    await safe_render(
        query,
        "📨 <b>Рассылка</b>\n\nОтправь текст или фото с подписью.",
        get_back_menu(),
    )


@router.message(Broadcast.content)
async def do_broadcast(message: Message, state: FSMContext) -> None:
    await state.clear()

    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User.telegram_id))).scalars().all()

    count = 0
    await message.answer(f"⏳ Рассылка для {len(users)}...")

    if message.photo:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        for uid in users:
            try:
                await message.bot.send_photo(
                    uid, file_id, caption=caption, parse_mode="HTML"
                )
                count += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
    else:
        for uid in users:
            try:
                await message.bot.send_message(uid, message.text, parse_mode="HTML")
                count += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass

    await message.answer(f"✅ Отправлено: {count}")


# ─────────────────────────────────────────────
# СТАТИСТИКА
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "stats"))
@require_admin
async def cb_stats(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        cards = (await session.execute(select(func.count(Card.id)))).scalar() or 0

    await safe_render(query, f"📊 Игроков: {users}\n🃏 Карт: {cards}", get_admin_menu())


# ─────────────────────────────────────────────
# БАЛАНС
# ─────────────────────────────────────────────

@router.message(Command("setbalance"))
async def cmd_setbalance(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Использование: <code>/setbalance @username сумма</code>",
            parse_mode="HTML",
        )
        return

    username = parts[1].lstrip("@").lower()

    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == username)
        )).scalar_one_or_none()

        if user is None:
            await message.answer("❌ Игрок не найден")
            return

        old = user.balance
        user.balance = amount
        await session.commit()
        name = user.username

    await message.answer(
        f"✅ <b>Баланс изменён</b>\n\n@{name}: {old} → <b>{amount}</b>",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# СОБЫТИЕ НА БИРЖЕ
# ─────────────────────────────────────────────

@router.message(Command("event"))
async def cmd_event(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Формат: <code>/event ID_КАРТЫ МОДИФИКАТОР</code>\n\n"
            "Пример: <code>/event 1 1.2</code> — карта #1 +20%",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])
        modifier = float(parts[2])
    except ValueError:
        await message.answer("❌ ID и модификатор — числа")
        return

    from services.market import Market

    async with AsyncSessionLocal() as session:
        new_price = await Market.apply_event(session, card_id, modifier)

    if new_price:
        await message.answer(f"✅ Карта #{card_id}: новая цена {new_price}")
    else:
        await message.answer("❌ Карта не найдена")


# ─────────────────────────────────────────────
# НАГРАДЫ ЗА БАЛАНС
# ─────────────────────────────────────────────

@router.callback_query(AdminMenu.filter(F.action == "rewards"))
@require_admin
async def cb_rewards(query: CallbackQuery) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "🏆 <b>Награды топ-5</b>\n\n"
        "Настрой через:\n"
        "<code>/setreward позиция тип значение</code>\n\n"
        "Типы: money, attempts, card\n"
        "Пример: <code>/setreward 1 money 10000</code>",
        get_admin_menu(),
    )


@router.message(Command("setreward"))
async def cmd_setreward(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS and message.from_user.id not in settings.ADMIN_IDS:
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "Формат: <code>/setreward позиция тип значение</code>",
            parse_mode="HTML",
        )
        return

    try:
        position = int(parts[1])
        rtype = parts[2]
        value = int(parts[3])
    except ValueError:
        await message.answer("❌ Позиция и значение — числа")
        return

    async with AsyncSessionLocal() as session:
        old = (await session.execute(
            select(Reward).where(Reward.position == position)
        )).scalar_one_or_none()

        if old is not None:
            await session.delete(old)

        session.add(Reward(position=position, reward_type=rtype, reward_value=value))
        await session.commit()

    await message.answer(f"✅ Награда для топ-{position}: {rtype} = {value}")


# ─────────────────────────────────────────────
# НАГРАДЫ PVP
# ─────────────────────────────────────────────

@router.message(Command("setpvpreward"))
async def cmd_setpvpreward(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.answer(
            "Формат: <code>/setpvpreward позиция деньги попытки [ID карты]</code>",
            parse_mode="HTML",
        )
        return

    try:
        position = int(parts[1])
        money = int(parts[2])
        attempts = int(parts[3])
        card_id = int(parts[4]) if len(parts) > 4 else None
    except ValueError:
        await message.answer("❌ Позиция, деньги, попытки и карта — числа")
        return

    async with AsyncSessionLocal() as session:
        old = (await session.execute(
            select(PvpReward).where(PvpReward.position == position)
        )).scalar_one_or_none()

        if old is not None:
            await session.delete(old)

        session.add(PvpReward(
            position=position,
            reward_money=money,
            reward_attempts=attempts,
            reward_card_id=card_id,
        ))
        await session.commit()

    card_text = f"\n🎴 Карта #{card_id}" if card_id else ""
    await message.answer(
        f"✅ PvP-награда для топ-{position}:\n"
        f"💰 {money} монет\n"
        f"🎴 {attempts} попыток{card_text}"
    )
