from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
import json

from core.config import settings
from core.constants import RARITIES, RARITY_NAMES, FLOOR_MULTIPLIER, CEILING_MULTIPLIER
from db.session import AsyncSessionLocal
from db.models import Card, User, PromoCode, PromoActivation

router = Router()


class AddCard(StatesGroup):
    name = State()
    rarity = State()
    team = State()
    year = State()
    price = State()
    image = State()


class AddPromo(StatesGroup):
    code = State()
    money = State()
    attempts = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "👑 <b>Панель P4/9</b>\n\n"
        "/addcard — конструктор карты\n"
        "/importcards — массовая загрузка (JSON)\n"
        "/addpromo — создать промокод\n"
        "/stats — статистика",
        parse_mode="HTML"
    )


# ─── КОНСТРУКТОР КАРТ ───

@router.message(Command("addcard"))
async def cmd_addcard(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCard.name)
    await message.answer("➕ <b>Конструктор карты</b>\n\nШаг 1/6: Имя пилота", parse_mode="HTML")


@router.message(AddCard.name)
async def ac_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCard.rarity)
    builder = InlineKeyboardBuilder()
    for r in RARITIES:
        builder.button(text=RARITY_NAMES[r], callback_data=f"rarity_{r}")
    builder.adjust(2)
    await message.answer("Шаг 2/6: Редкость:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("rarity_"))
async def ac_rarity(query: CallbackQuery, state: FSMContext):
    rarity = query.data.replace("rarity_", "")
    await state.update_data(rarity=rarity)
    await state.set_state(AddCard.team)
    await query.answer()
    await query.message.edit_text("Шаг 3/6: Команда")


@router.message(AddCard.team)
async def ac_team(message: Message, state: FSMContext):
    await state.update_data(team=message.text.strip())
    await state.set_state(AddCard.year)
    await message.answer("Шаг 4/6: Год")


@router.message(AddCard.year)
async def ac_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Год — число")
        return
    await state.update_data(year=year)
    await state.set_state(AddCard.price)
    await message.answer("Шаг 5/6: Начальная цена")


@router.message(AddCard.price)
async def ac_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Цена — число")
        return
    await state.update_data(price=price)
    await state.set_state(AddCard.image)
    await message.answer(
        "Шаг 6/6: Отправь <b>фото</b> или <code>skip</code>",
        parse_mode="HTML"
    )


@router.message(AddCard.image, F.photo)
async def ac_image(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    async with AsyncSessionLocal() as session:
        session.add(Card(
            name=data["name"], rarity=data["rarity"], team=data["team"],
            year=data["year"], base_price=data["price"], current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            image_file_id=file_id, created_by=message.from_user.id,
        ))
        await session.commit()
    await message.answer(f"✅ <b>Карта добавлена!</b>\n{data['name']} — {RARITY_NAMES[data['rarity']]}", parse_mode="HTML")


@router.message(AddCard.image, F.text == "skip")
async def ac_image_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    async with AsyncSessionLocal() as session:
        session.add(Card(
            name=data["name"], rarity=data["rarity"], team=data["team"],
            year=data["year"], base_price=data["price"], current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            image_file_id=None, created_by=message.from_user.id,
        ))
        await session.commit()
    await message.answer(f"✅ <b>Карта добавлена (без фото)!</b>", parse_mode="HTML")


# ─── МАССОВАЯ ЗАГРУЗКА ───

@router.message(Command("importcards"))
async def cmd_importcards(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📦 <b>Массовая загрузка</b>\n\n"
        "Отправь JSON-файл с картами.\n\n"
        "<b>Формат:</b>\n"
        '<pre>[{"name": "Alex Palou", "rarity": "epic", "team": "Ganassi", "year": 2026, "base_price": 1000, "image_file_id": "..."}]</pre>',
        parse_mode="HTML"
    )


@router.message(F.document)
async def handle_import(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not message.document.file_name.endswith(".json"):
        return

    file = await message.bot.get_file(message.document.file_id)
    content = await message.bot.download_file(file.file_path)
    data = json.loads(content.read().decode("utf-8"))

    if not isinstance(data, list):
        await message.answer("❌ JSON должен быть массивом карт.")
        return

    async with AsyncSessionLocal() as session:
        count = 0
        for item in data:
            base = item.get("base_price", 100)
            session.add(Card(
                name=item["name"], rarity=item["rarity"], team=item.get("team"),
                year=item.get("year"), base_price=base, current_price=base,
                floor_price=int(base * FLOOR_MULTIPLIER),
                ceiling_price=int(base * CEILING_MULTIPLIER),
                image_file_id=item.get("image_file_id"),
                created_by=message.from_user.id,
            ))
            count += 1
        await session.commit()

    await message.answer(f"✅ <b>Загружено: {count} карт</b>", parse_mode="HTML")


# ─── ПРОМОКОДЫ ───

@router.message(Command("addpromo"))
async def cmd_addpromo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddPromo.code)
    await message.answer("🎁 <b>Новый промокод</b>\n\nШаг 1/3: Код (например, ILOVEINDYCARTS)")


@router.message(AddPromo.code)
async def ap_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AddPromo.money)
    await message.answer("Шаг 2/3: Сколько монет?")


@router.message(AddPromo.money)
async def ap_money(message: Message, state: FSMContext):
    try:
        money = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    await state.update_data(money=money)
    await state.set_state(AddPromo.attempts)
    await message.answer("Шаг 3/3: Сколько попыток?")


@router.message(AddPromo.attempts)
async def ap_attempts(message: Message, state: FSMContext):
    try:
        attempts = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return
    data = await state.get_data()
    await state.clear()
    async with AsyncSessionLocal() as session:
        session.add(PromoCode(
            code=data["code"], reward_money=data["money"],
            reward_attempts=attempts, created_by=message.from_user.id,
        ))
        await session.commit()
    await message.answer(f"✅ Промокод <code>{data['code']}</code> создан", parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        cards = (await session.execute(select(func.count(Card.id)))).scalar() or 0
    await message.answer(f"📊 Игроков: {users}\n🃏 Карт: {cards}", parse_mode="HTML")
