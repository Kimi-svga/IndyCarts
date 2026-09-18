"""Управление ролями: найм админов через панель."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from bot.utils.decorators import require_owner
from core.config import settings
from db.session import AsyncSessionLocal
from db.models import User, AdminRole

router = Router()


class RolesMenu(CallbackData, prefix="roles"):
    action: str


class HireState(StatesGroup):
    waiting_username = State()


@router.callback_query(MainMenu.filter(F.action == "admin_panel"))
@require_owner
async def cb_admin_panel(query: CallbackQuery):
    b = InlineKeyboardBuilder()
    b.button(text="➕ Нанять админа", callback_data=RolesMenu(action="hire"))
    b.button(text="👥 Список админов", callback_data=RolesMenu(action="list"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)

    await safe_render(query, "👑 <b>Панель владельца</b>\n\nУправление админами:", b.as_markup())


@router.callback_query(RolesMenu.filter(F.action == "hire"))
@require_owner
async def cb_hire(query: CallbackQuery, state: FSMContext):
    await state.set_state(HireState.waiting_username)
    await safe_render(query, "➕ <b>Найм админа</b>\n\nВведи юз игрока (без @):", get_back_menu())


@router.message(HireState.waiting_username)
async def hire_username(message: Message, state: FSMContext):
    if message.from_user.id not in settings.OWNER_IDS:
        return

    username = message.text.strip().lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.username_normalized == username))).scalar_one_or_none()
        if not user:
            await message.answer("❌ Игрок не найден")
            return

        existing = (await session.execute(select(AdminRole).where(AdminRole.user_id == user.id))).scalar_one_or_none()
        if existing:
            await message.answer(f"❌ @{username} уже {existing.role}")
            return

        session.add(AdminRole(user_id=user.id, role="admin", appointed_by=message.from_user.id))
        await session.commit()
        user_tg = user.telegram_id

    await state.clear()
    await message.answer(f"✅ @{username} назначен <b>admin</b>", parse_mode="HTML")

    try:
        await message.bot.send_message(
            user_tg,
            f"👑 <b>Ты назначен админом!</b>\n\nДоступ к панели: /admin",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(RolesMenu.filter(F.action == "list"))
@require_owner
async def cb_admins_list(query: CallbackQuery):
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(AdminRole, User).join(User, AdminRole.user_id == User.id)
        )).all()

    if not rows:
        text = "👥 <b>Админов нет</b>"
    else:
        text = "👥 <b>Команда</b>\n\n"
        for role, user in rows:
            emoji = "👑" if role.role == "admin" else "🛡"
            text += f"{emoji} @{user.username} — <b>{role.role}</b>\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RolesMenu(action="back_to_panel"))
    b.adjust(1)
    await safe_render(query, text, b.as_markup())


@router.callback_query(RolesMenu.filter(F.action == "back_to_panel"))
async def cb_back_panel(query: CallbackQuery):
    await safe_answer(query)
    await cb_admin_panel(query) 
