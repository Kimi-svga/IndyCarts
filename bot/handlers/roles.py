"""Управление ролями: /hire, /fire, /admins, /adminrole + панель."""

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.decorators import require_owner
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import ROLE_EMOJI, ROLE_LEVELS, ROLE_NAMES
from core.logger import setup_logger
from db.models import AdminRole, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


class RolesMenu(CallbackData, prefix="roles"):
    action: str


# ═════════════════════════════════════════════
# ПАНЕЛЬ ВЛАДЕЛЬЦА
# ═════════════════════════════════════════════

def _panel_keyboard() -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Нанять админа", callback_data=RolesMenu(action="hire").pack())
    b.button(text="👥 Команда", callback_data=RolesMenu(action="list").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b


async def _show_panel(query: CallbackQuery) -> None:
    await safe_render(
        query,
        "👑 <b>Панель владельца</b>\n\n"
        "Управление командой и ролями.",
        _panel_keyboard().as_markup(),
    )


@router.callback_query(MainMenu.filter(F.action == "admin_panel"))
@require_owner
async def cb_admin_panel(query: CallbackQuery) -> None:
    await safe_answer(query)
    await _show_panel(query)


@router.callback_query(RolesMenu.filter(F.action == "back"))
@require_owner
async def cb_back_to_panel(query: CallbackQuery) -> None:
    await safe_answer(query)
    await _show_panel(query)


# ─── Найм ───

@router.callback_query(RolesMenu.filter(F.action == "hire"))
@require_owner
async def cb_hire(query: CallbackQuery) -> None:
    await safe_answer(query)

    b = InlineKeyboardBuilder()
    b.button(text="🔴 Admin", callback_data=RolesMenu(action="role_admin").pack())
    b.button(text="🟡 Moderator", callback_data=RolesMenu(action="role_moderator").pack())
    b.button(text="🟢 Helper", callback_data=RolesMenu(action="role_helper").pack())
    b.button(text="🔵 Support", callback_data=RolesMenu(action="role_support").pack())
    b.button(text="🔙 Назад", callback_data=RolesMenu(action="back").pack())
    b.adjust(2, 2, 1)

    await safe_render(
        query,
        "➕ <b>Найм админа</b>\n\n"
        "Выбери роль — потом введи ник командой:\n\n"
        "<code>/hire @username роль</code>",
        b.as_markup(),
    )


@router.callback_query(RolesMenu.filter(F.action.startswith("role_")))
@require_owner
async def cb_hire_role(query: CallbackQuery, callback_data: RolesMenu) -> None:
    await safe_answer(query)
    role = callback_data.action.replace("role_", "")

    if role not in ROLE_LEVELS or role == "owner":
        return

    emoji = ROLE_EMOJI.get(role, "•")
    name = ROLE_NAMES.get(role, role)

    await safe_render(
        query,
        f"{emoji} <b>Найм: {name}</b>\n\n"
        f"Отправь команду:\n"
        f"<code>/hire @username {role}</code>",
        get_back_menu(),
    )


# ─── Список ───

@router.callback_query(RolesMenu.filter(F.action == "list"))
@require_owner
async def cb_list(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(AdminRole, User)
            .join(User, AdminRole.user_id == User.id)
            .where(AdminRole.is_active == True)
            .order_by(AdminRole.role)
        )).all()

        owner_users = (await session.execute(
            select(User).where(User.telegram_id.in_(settings.OWNER_IDS))
        )).scalars().all()

    text = "👑 <b>Команда Indy Carts</b>\n\n"

    if owner_users:
        text += "<b>Владельцы:</b>\n"
        for u in owner_users:
            text += f"👑 @{u.username}\n"
        text += "\n"

    by_role: dict[str, list[str]] = {}
    for role_obj, user in rows:
        by_role.setdefault(role_obj.role, []).append(user.username)

    if not by_role:
        text += "<i>Команда пуста</i>\n"
    else:
        for rc in ["admin", "moderator", "helper", "support"]:
            users = by_role.get(rc, [])
            if users:
                emoji = ROLE_EMOJI.get(rc, "•")
                text += f"<b>{ROLE_NAMES[rc]}:</b>\n"
                for u in users:
                    text += f"{emoji} @{u}\n"
                text += "\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RolesMenu(action="back").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


# ═════════════════════════════════════════════
# КОМАНДЫ
# ═════════════════════════════════════════════

@router.message(Command("hire"))
async def cmd_hire(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        await message.answer("⛔ Только владелец")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Формат: <code>/hire @username role</code>\n\n"
            "Роли: admin / moderator / helper / support",
            parse_mode="HTML",
        )
        return

    target = parts[1].lstrip("@").lower()
    role = parts[2].lower()

    if role not in ROLE_LEVELS or role == "owner":
        await message.answer("❌ Неверная роль")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        # Кто назначает — из БД (не telegram_id!)
        mod_user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()
        mod_user_id = mod_user.id if mod_user else None

        existing = (await session.execute(
            select(AdminRole).where(AdminRole.user_id == user.id)
        )).scalar_one_or_none()

        if existing:
            if existing.role == role and existing.is_active:
                await message.answer(f"❌ @{target} уже {ROLE_NAMES[role]}")
                return
            existing.role = role
            existing.is_active = True
            existing.appointed_by = mod_user_id
            existing.updated_at = datetime.utcnow()
        else:
            session.add(AdminRole(
                user_id=user.id,
                role=role,
                appointed_by=mod_user_id,
                is_active=True,
            ))

        await session.commit()
        target_tg = user.telegram_id
        username = user.username

    emoji = ROLE_EMOJI.get(role, "•")
    await message.answer(
        f"✅ @{username} назначен {emoji} <b>{ROLE_NAMES[role]}</b>",
        parse_mode="HTML",
    )

    try:
        await message.bot.send_message(
            target_tg,
            f"{emoji} <b>Ты назначен {ROLE_NAMES[role]}!</b>\n\n"
            f"Доступ к панели: /admin",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.message(Command("fire"))
async def cmd_fire(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        await message.answer("⛔ Только владелец")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/fire @username</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        role = (await session.execute(
            select(AdminRole).where(AdminRole.user_id == user.id)
        )).scalar_one_or_none()

        if role is None or not role.is_active:
            await message.answer(f"❌ @{target} не админ")
            return

        role.is_active = False
        role.updated_at = datetime.utcnow()

        await session.commit()
        target_tg = user.telegram_id
        username = user.username

    await message.answer(f"✅ @{username} снят с должности")

    try:
        await message.bot.send_message(
            target_tg,
            "🚫 <b>Ты больше не админ.</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.message(Command("admins"))
async def cmd_admins(message: Message) -> None:
    from bot.utils.decorators import check_role
    if not await check_role(message.from_user.id, "moderator"):
        await message.answer("⛔ Нет доступа")
        return

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(AdminRole, User)
            .join(User, AdminRole.user_id == User.id)
            .where(AdminRole.is_active == True)
            .order_by(AdminRole.role)
        )).all()

        owner_users = (await session.execute(
            select(User).where(User.telegram_id.in_(settings.OWNER_IDS))
        )).scalars().all()

    text = "👑 <b>Команда Indy Carts</b>\n\n"

    if owner_users:
        text += "<b>Владельцы:</b>\n"
        for u in owner_users:
            text += f"👑 @{u.username}\n"
        text += "\n"

    by_role: dict[str, list[str]] = {}
    for role_obj, user in rows:
        by_role.setdefault(role_obj.role, []).append(user.username)

    for rc in ["admin", "moderator", "helper", "support"]:
        users = by_role.get(rc, [])
        if users:
            emoji = ROLE_EMOJI.get(rc, "•")
            text += f"<b>{ROLE_NAMES[rc]}:</b>\n"
            for u in users:
                text += f"{emoji} @{u}\n"
            text += "\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("adminrole"))
async def cmd_adminrole(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/adminrole @username</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        role = (await session.execute(
            select(AdminRole).where(AdminRole.user_id == user.id)
        )).scalar_one_or_none()

    if role is None or not role.is_active:
        await message.answer(f"👤 @{user.username} — не админ")
        return

    emoji = ROLE_EMOJI.get(role.role, "•")
    text = (
        f"👤 <b>@{user.username}</b>\n\n"
        f"{emoji} Роль: <b>{ROLE_NAMES.get(role.role, role.role)}</b>\n"
        f"📅 Назначен: {role.appointed_at.strftime('%d.%m.%Y')}\n"
    )
    if role.notes:
        text += f"📝 Заметки: {role.notes}\n"

    await message.answer(text, parse_mode="HTML") 
