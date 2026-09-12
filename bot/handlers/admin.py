from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.config import settings
from core.constants import (
    RARITIES, RARITY_NAMES, BASE_PRICES,
    FLOOR_MULTIPLIER, CEILING_MULTIPLIER
)
from db.session import AsyncSessionLocal
from db.models import Card

router = Router()


class AddCard(StatesGroup):
    name = State()
    rarity = State()
    team = State()
    year = State()
    base_price = State()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer(
        "👑 <b>Панель P4/9</b>\n\n"
        "Команды:\n"
        "/addcard — добавить карту\n"
        "/stats — статистика",
        parse_mode="HTML"
    )


@router.message(Command("addcard"))
async def cmd_add_card(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCard.name)
    await message.answer("➕ <b>Новая карта</b>\n\nШаг 1/5: Имя пилота", parse_mode="HTML")


@router.message(AddCard.name)
async def ac_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddCard.rarity)

    builder = InlineKeyboardBuilder()
    for r in RARITIES:
        builder.button(text=RARITY_NAMES[r], callback_data=f"rarity_{r}")
    builder.adjust(2)

    await message.answer("Шаг 2/5: Редкость:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("rarity_"))
async def ac_rarity(query: CallbackQuery, state: FSMContext):
    rarity = query.data.replace("rarity_", "")
    await state.update_data(rarity=rarity)
    await state.set_state(AddCard.team)
    await query.answer()
    await query.message.edit_text("Шаг 3/5: Команда")


@router.message(AddCard.team)
async def ac_team(message: Message, state: FSMContext):
    await state.update_data(team=message.text.strip())
    await state.set_state(AddCard.year)
    await message.answer("Шаг 4/5: Год")


@router.message(AddCard.year)
async def ac_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Год — число")
        return
    await state.update_data(year=year)
    await state.set_state(AddCard.base_price)
    await message.answer("Шаг 5/5: Начальная цена")


@router.message(AddCard.base_price)
async def ac_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Цена — число")
        return

    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        card = Card(
            name=data["name"],
            rarity=data["rarity"],
            team=data["team"],
            year=data["year"],
            base_price=price,
            current_price=price,
            floor_price=int(price * FLOOR_MULTIPLIER),
            ceiling_price=int(price * CEILING_MULTIPLIER),
            created_by=message.from_user.id,
        )
        session.add(card)
        await session.commit()

    await message.answer(
        f"✅ <b>Карта добавлена!</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Редкость: {RARITY_NAMES[data['rarity']]}\n"
        f"Цена: {price}",
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        from db.models import User as U

        users_count = (await session.execute(select(func.count(U.id)))).scalar() or 0
        cards_count = (await session.execute(select(func.count(Card.id)))).scalar() or 0

    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Игроков: {users_count}\n"
        f"🃏 Карт: {cards_count}",
        parse_mode="HTML"
  ) 
