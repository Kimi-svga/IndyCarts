from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func

from core.config import settings
from core.constants import RARITIES, RARITY_NAMES, FLOOR_MULTIPLIER, CEILING_MULTIPLIER
from db.session import AsyncSessionLocal
from db.models import Card, User

router = Router()


class AddCard(StatesGroup):
    name = State()
    rarity = State()
    team = State()
    year = State()
    price = State()
    image = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer(
        "👑 <b>Панель P4/9</b>\n\n"
        "/addcard — добавить карту\n"
        "/stats — статистика",
        parse_mode="HTML"
    )


@router.message(Command("addcard"))
async def cmd_addcard(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCard.name)
    await message.answer("➕ <b>Новая карта</b>\n\nШаг 1/6: Имя пилота", parse_mode="HTML")


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
        "Шаг 6/6: Отправь <b>фото карточки</b>.\n"
        "Или напиши <code>skip</code>, чтобы без фото.",
        parse_mode="HTML"
    )


@router.message(AddCard.image, F.photo)
async def ac_image(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        session.add(Card(
            name=data["name"],
            rarity=data["rarity"],
            team=data["team"],
            year=data["year"],
            base_price=data["price"],
            current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            image_file_id=file_id,
            created_by=message.from_user.id,
        ))
        await session.commit()

    await message.answer(
        f"✅ <b>Карта добавлена с фото!</b>\n\n"
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
        session.add(Card(
            name=data["name"],
            rarity=data["rarity"],
            team=data["team"],
            year=data["year"],
            base_price=data["price"],
            current_price=data["price"],
            floor_price=int(data["price"] * FLOOR_MULTIPLIER),
            ceiling_price=int(data["price"] * CEILING_MULTIPLIER),
            image_file_id=None,
            created_by=message.from_user.id,
        ))
        await session.commit()

    await message.answer(
        f"✅ <b>Карта добавлена (без фото)</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Редкость: {RARITY_NAMES[data['rarity']]}",
        parse_mode="HTML"
    )


@router.message(AddCard.image)
async def ac_image_invalid(message: Message):
    await message.answer("❌ Отправь фото или <code>skip</code>", parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        cards = (await session.execute(select(func.count(Card.id)))).scalar() or 0
    await message.answer(f"📊 Игроков: {users}\n🃏 Карт: {cards}", parse_mode="HTML")
