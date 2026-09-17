"""
Админ-панель P4/9.
Конструктор карт, промокоды, рассылка, статистика.
"""
import asyncio
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func

from core.config import settings
from core.constants import (
    RARITIES, RARITY_NAMES, FLOOR_MULTIPLIER,
    CEILING_MULTIPLIER, BASE_PRICES
)
from db.session import AsyncSessionLocal
from db.models import Card, User, PromoCode

router = Router()


# ─── FSM состояния ───

class AddCard(StatesGroup):
    name = State()
    rarity = State()
    team = State()
    year = State()
    price = State()
    weight = State()
    image = State()


class AddPromo(StatesGroup):
    code = State()
    money = State()
    attempts = State()


class Broadcast(StatesGroup):
    text = State()


def is_admin(user_id: int) -> bool:
    """Проверка, админ ли пользователь."""
    return user_id in settings.ADMIN_IDS


# ─── Главная админка ───

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer(
        "👑 <b>Панель P4/9</b>\n\n"
        "<b>Команды:</b>\n"
        "/addcard — добавить карту\n"
        "/importcards — массовая загрузка (JSON)\n"
        "/addpromo — создать промокод\n"
        "/broadcast — рассылка\n"
        "/stats — статистика",
        parse_mode="HTML"
    )


# ─── Конструктор карт ───

@router.message(Command("addcard"))
async def cmd_addcard(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCard.name)
    await message.answer("➕ <b>Конструктор карты</b>\n\nШаг 1/7: Имя пилота", parse_mode="HTML")


@router.message(AddCard.name)
async def ac_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Отправь текст")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCard.rarity)

    builder = InlineKeyboardBuilder()
    for rarity in RARITIES:
        builder.button(
            text=RARITY_NAMES[rarity],
            callback_data=f"rarity_{rarity}"
        )
    builder.adjust(2)

    await message.answer("Шаг 2/7: Редкость", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("rarity_"))
async def ac_rarity(query: CallbackQuery, state: FSMContext):
    rarity = query.data.replace("rarity_", "")
    if rarity not in RARITIES:
        await query.answer("❌ Неверная редкость", show_alert=True)
        return

    await state.update_data(rarity=rarity)
    await state.set_state(AddCard.team)
    await query.answer()
    await query.message.edit_text("Шаг 3/7: Команда (например: Chip Ganassi Racing)")


@router.message(AddCard.team)
async def ac_team(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Отправь текст")
        return
    await state.update_data(team=message.text.strip())
    await state.set_state(AddCard.year)
    await message.answer("Шаг 4/7: Год (например: 2026)")


@router.message(AddCard.year)
async def ac_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Год — число")
        return
    await state.update_data(year=year)
    await state.set_state(AddCard.price)
    await message.answer("Шаг 5/7: Начальная цена (например: 1000)")


@router.message(AddCard.price)
async def ac_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Цена — число")
        return
    if price <= 0:
        await message.answer("❌ Цена должна быть больше 0")
        return
    await state.update_data(price=price)
    await state.set_state(AddCard.weight)
    await message.answer(
        "Шаг 6/7: Вес дропа\n"
        "100 — стандарт\n"
        "Больше — чаще падает\n"
        "Меньше — реже падает"
    )


@router.message(AddCard.weight)
async def ac_weight(message: Message, state: FSMContext):
    try:
        weight = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Вес — число")
        return
    if weight <= 0:
        await message.answer("❌ Вес должен быть больше 0")
        return
    await state.update_data(weight=weight)
    await state.set_state(AddCard.image)
    await message.answer(
        "Шаг 7/7: Отправь <b>фото карточки</b>\n"
        "Или напиши <code>skip</code>, чтобы без фото.",
        parse_mode="HTML"
    )


@router.message(AddCard.image, F.photo)
async def ac_image(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = Card(
            name=data["name"],
            rarity=data["rarity"],
            team=data["team"],
            year=data["year"],
            base_price=data["price"],
            current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            drop_weight=data["weight"],
            image_file_id=file_id,
            created_by=message.from_user.id,
        )
        session.add(card)
        await session.commit()

    await message.answer(
        f"✅ <b>Карта добавлена!</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Редкость: {RARITY_NAMES[data['rarity']]}\n"
        f"Цена: {data['price']}",
        parse_mode="HTML"
    )


@router.message(AddCard.image, F.text == "skip")
async def ac_image_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = Card(
            name=data["name"],
            rarity=data["rarity"],
            team=data["team"],
            year=data["year"],
            base_price=data["price"],
            current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            drop_weight=data["weight"],
            image_file_id=None,
            created_by=message.from_user.id,
        )
        session.add(card)
        await session.commit()

    await message.answer(
        f"✅ <b>Карта добавлена (без фото)!</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Редкость: {RARITY_NAMES[data['rarity']]}\n"
        f"Цена: {data['price']}",
        parse_mode="HTML"
    )


@router.message(AddCard.image)
async def ac_image_invalid(message: Message):
    await message.answer("❌ Отправь фото или <code>skip</code>", parse_mode="HTML")


# ─── Массовая загрузка карт ───

@router.message(Command("importcards"))
async def cmd_import(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📦 <b>Массовая загрузка карт</b>\n\n"
        "Отправь JSON-файл со списком карт.\n\n"
        "<b>Формат:</b>\n"
        '<pre>[{"name": "Alex Palou", "rarity": "epic", "team": "Ganassi", "year": 2026, "base_price": 1000, "drop_weight": 100, "image_file_id": "..."}]</pre>',
        parse_mode="HTML"
    )


@router.message(F.document)
async def handle_import(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not message.document.file_name.endswith(".json"):
        await message.answer("❌ Нужен JSON-файл")
        return

    try:
        file = await message.bot.get_file(message.document.file_id)
        content = await message.bot.download_file(file.file_path)
        data = json.loads(content.read().decode("utf-8"))
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения файла: {e}")
        return

    if not isinstance(data, list):
        await message.answer("❌ JSON должен быть массивом карт")
        return

    count = 0
    errors = 0

    async with AsyncSessionLocal() as session:
        for item in data:
            try:
                base = int(item.get("base_price", 100))
                card = Card(
                    name=item["name"],
                    rarity=item["rarity"],
                    team=item.get("team"),
                    year=item.get("year"),
                    base_price=base,
                    current_price=base,
                    floor_price=int(base * FLOOR_MULTIPLIER),
                    ceiling_price=int(base * CEILING_MULTIPLIER),
                    drop_weight=item.get("drop_weight", 100),
                    image_file_id=item.get("image_file_id"),
                    created_by=message.from_user.id,
                )
                session.add(card)
                count += 1
            except Exception as e:
                errors += 1
                continue

        await session.commit()

    await message.answer(
        f"✅ <b>Загружено: {count} карт</b>\n"
        f"❌ Ошибок: {errors}",
        parse_mode="HTML"
    )


# ─── Промокоды ───

@router.message(Command("addpromo"))
async def cmd_addpromo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddPromo.code)
    await message.answer("🎁 <b>Новый промокод</b>\n\nШаг 1/3: Код (например: ILOVEINDYCARTS)")


@router.message(AddPromo.code)
async def ap_code(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Отправь текст")
        return
    code = message.text.strip().upper()
    if len(code) < 3 or len(code) > 32:
        await message.answer("❌ Код от 3 до 32 символов")
        return

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(PromoCode).where(PromoCode.code == code)
        )).scalar_one_or_none()
        if existing:
            await message.answer("❌ Такой промокод уже существует")
            return

    await state.update_data(code=code)
    await state.set_state(AddPromo.money)
    await message.answer("Шаг 2/3: Сколько монет выдавать?")


@router.message(AddPromo.money)
async def ap_money(message: Message, state: FSMContext):
    try:
        money = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Число")
        return
    if money < 0:
        await message.answer("❌ Не может быть отрицательным")
        return
    await state.update_data(money=money)
    await state.set_state(AddPromo.attempts)
    await message.answer("Шаг 3/3: Сколько попыток выдавать?")


@router.message(AddPromo.attempts)
async def ap_attempts(message: Message, state: FSMContext):
    try:
        attempts = int(message.text.strip())
    except (ValueError, AttributeError):
        await message.answer("❌ Число")
        return
    if attempts < 0:
        await message.answer("❌ Не может быть отрицательным")
        return

    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        promo = PromoCode(
            code=data["code"],
            reward_money=data["money"],
            reward_attempts=attempts,
        )
        session.add(promo)
        await session.commit()

    await message.answer(
        f"✅ <b>Промокод создан!</b>\n\n"
        f"Код: <code>{data['code']}</code>\n"
        f"💰 Монеты: {data['money']}\n"
        f"🎴 Попытки: {attempts}",
        parse_mode="HTML"
    )


# ─── Рассылка ───

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.text)
    await message.answer(
        "📨 <b>Рассылка</b>\n\n"
        "Отправь текст, который получат все игроки.\n"
        "Поддерживается HTML-разметка.",
        parse_mode="HTML"
    )


@router.message(Broadcast.text)
async def do_broadcast(message: Message, state: FSMContext):
    await state.clear()

    if not message.text:
        await message.answer("❌ Отправь текст")
        return

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User.telegram_id)
        )).scalars().all()

    if not users:
        await message.answer("⚠️ Нет игроков для рассылки")
        return

    status = await message.answer(f"⏳ Рассылка для {len(users)} игроков...")

    success = 0
    failed = 0

    for uid in users:
        try:
            await message.bot.send_message(uid, message.text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05)  # защита от лимитов Telegram
        except Exception:
            failed += 1

    await status.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Отправлено: <b>{success}</b>\n"
        f"Ошибок: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ─── Статистика ───

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        users_count = (await session.execute(
            select(func.count(User.id))
        )).scalar() or 0

        cards_count = (await session.execute(
            select(func.count(Card.id))
        )).scalar() or 0

        active_count = (await session.execute(
            select(func.count(User.id)).where(User.daily_attempts > 0)
        )).scalar() or 0

        total_money = (await session.execute(
            select(func.sum(User.balance))
        )).scalar() or 0

    await message.answer(
        f"📊 <b>Статистика Indy Carts</b>\n\n"
        f"👥 Игроков: <b>{users_count}</b>\n"
        f"🟢 Активных: <b>{active_count}</b>\n"
        f"🃏 Карт в базе: <b>{cards_count}</b>\n"
        f"💰 Денежная масса: <b>{total_money:,}</b>",
        parse_mode="HTML"
    ) 
