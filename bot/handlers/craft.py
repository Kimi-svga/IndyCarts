"""Обработчик крафта карт и создания рецептов (Админка)."""

import json
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.cards import CardsMenu
from bot.keyboards.main import get_back_menu
from bot.utils.decorators import check_role
from bot.utils.stable import safe_answer, safe_render
from db.models import Card, CraftRecipe, User
from db.session import AsyncSessionLocal
from services.craft import craft_card, get_available_recipes

router = Router()

class CraftState(StatesGroup):
    waiting_name = State()
    waiting_result_card = State()
    waiting_ingredients = State()

@router.callback_query(CardsMenu.filter(F.action == "craft"))
async def cb_craft_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    
    async with AsyncSessionLocal() as session:
        recipes = await get_available_recipes(session)
        
    text = "🛠 <b>Крафт карт</b>\n\nВыбери рецепт, чтобы узнать, что нужно сдать:"
    b = InlineKeyboardBuilder()
    
    if not recipes:
        text += "\n\n<i>Пока нет доступных рецептов.</i>"
    else:
        for r in recipes:
            b.button(text=f"📜 {r.name}", callback_data=f"craft_view_{r.id}")
            
    if await check_role(query.from_user.id, "admin"):
        b.button(text="➕ Создать рецепт (Админ)", callback_data="craft_admin_create")
        
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back_to_cards"))
    b.adjust(1)
    await safe_render(query, text, b.as_markup())

@router.callback_query(F.data.startswith("craft_view_"))
async def cb_craft_view(query: CallbackQuery) -> None:
    await safe_answer(query)
    recipe_id = int(query.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        recipe = await session.get(CraftRecipe, recipe_id)
        if not recipe: return
            
        result_card = await session.get(Card, recipe.result_card_id)
        ingredients_ids = json.loads(recipe.ingredients)
        
        ingredients_text = ""
        for cid in ingredients_ids:
            c = await session.get(Card, cid)
            if c:
                ingredients_text += f"• {c.name}\n"
                
    text = (
        f"📜 <b>Рецепт: {recipe.name}</b>\n\n"
        f"<b>Нужно сдать:</b>\n{ingredients_text}\n"
        f"<b>Получишь:</b>\n✨ {result_card.name}\n\n"
        f"Скрафтить?"
    )
    b = InlineKeyboardBuilder()
    b.button(text="✅ Скрафтить", callback_data=f"craft_do_{recipe.id}")
    b.button(text="🔙 К рецептам", callback_data=CardsMenu(action="craft"))
    b.adjust(1)
    await safe_render(query, text, b.as_markup())

@router.callback_query(F.data.startswith("craft_do_"))
async def cb_craft_do(query: CallbackQuery) -> None:
    await safe_answer(query, "Крафтим...")
    recipe_id = int(query.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if not user: return
            
        result = await craft_card(session, user.id, recipe_id)
        
    if not result.ok:
        await query.answer(result.reason, show_alert=True)
        return
        
    await safe_render(
        query,
        f"✅ <b>Успех!</b>\n\nТы создал особую карту: <b>{result.card_name}</b>",
        get_back_menu()
    )

@router.callback_query(F.data == "craft_admin_create")
async def cb_craft_admin(query: CallbackQuery, state: FSMContext) -> None:
    if not await check_role(query.from_user.id, "admin"): return
    await safe_answer(query)
    await state.set_state(CraftState.waiting_name)
    
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data=CardsMenu(action="craft"))
    await safe_render(query, "🛠 <b>Шаг 1/3</b>\n\nВведи название рецепта:", b.as_markup())

@router.message(CraftState.waiting_name)
async def craft_wait_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(CraftState.waiting_result_card)
    await message.answer("🛠 <b>Шаг 2/3</b>\n\nВведи ID карты, которая получится в результате:", parse_mode="HTML")

@router.message(CraftState.waiting_result_card)
async def craft_wait_result(message: Message, state: FSMContext) -> None:
    try:
        card_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)
        if not card:
            await message.answer("❌ Карта с таким ID не найдена")
            return
    await state.update_data(result_card_id=card_id)
    await state.set_state(CraftState.waiting_ingredients)
    await message.answer("🛠 <b>Шаг 3/3</b>\n\nВведи ID карт, которые нужно сдать, через запятую:", parse_mode="HTML")

@router.message(CraftState.waiting_ingredients)
async def craft_wait_ingredients(message: Message, state: FSMContext) -> None:
    try:
        ids = [int(x.strip()) for x in message.text.split(",")]
    except ValueError:
        await message.answer("❌ Неверный формат. Введи числа через запятую.")
        return
    data = await state.get_data()
    await state.clear()
    async with AsyncSessionLocal() as session:
        for cid in ids:
            if not await session.get(Card, cid):
                await message.answer(f"❌ Карта с ID {cid} не найдена. Рецепт отменен.")
                return
        recipe = CraftRecipe(
            name=data["name"],
            result_card_id=data["result_card_id"],
            ingredients=json.dumps(ids),
            is_active=True
        )
        session.add(recipe)
        await session.commit()
    await message.answer(
        f"✅ <b>Рецепт «{data['name']}» создан!</b>",
        parse_mode="HTML",
        reply_markup=get_back_menu()
)
