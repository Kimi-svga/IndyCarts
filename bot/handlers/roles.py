"""Управление ролями: /hire, /fire, /admins, /adminrole."""

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu
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


@router.message(Command("hire"))
async def cmd_hire(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS:
        await message.answer("⛔ Только владелец")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Формат: <code>/hire @username role</code>\n\n"
            "Роли: <code>admin</code> / <code>moderator</code> / "
            "<code>helper</code> / <code>support</code>",
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

        existing = (await session.execute(
            select(AdminRole).where(AdminRole.user_id == user.id)
        )).scalar_one_or_none()

        if existing:
            if existing.role == role and existing.is_active:
                await message.answer(f"❌ @{target} уже {ROLE_NAMES[role]}")
                return
            existing.role = role
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
        else:
            session.add(AdminRole(
                user_id=user.id,
                role=role,
                appointed_by=message.from_user.id,
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

    text = "👑 <b>Команда Indy Carts</b>\n\n"

    owners = [f"👑 @{uid}" for uid in settings.OWNER_IDS]
    if owners:
        text += "<b>Владельцы:</b>\n" + "\n".join(owners) + "\n\n"

    by_role: dict[str, list[str]] = {}
    for role_obj, user in rows:
        by_role.setdefault(role_obj.role, []).append(user.username)

    for role_code in ["admin", "moderator", "helper", "support"]:
        users = by_role.get(role_code, [])
        if users:
            emoji = ROLE_EMOJI.get(role_code, "•")
            text += f"<b>{ROLE_NAMES[role_code]}:</b>\n"
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


@router.callback_query(MainMenu.filter(F.action == "admin_panel"))
@require_owner
async def cb_admin_panel(query: CallbackQuery) -> None:
    await safe_answer(query)
    b = InlineKeyboardBuilder()
    b.button(text="➕ Нанять", callback_data=RolesMenu(action="hire").pack())
    b.button(text="👥 Команда", callback_data=RolesMenu(action="list").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(2, 1)
    await safe_render(query, "👑 <b>Панель владельца</b>", b.as_markup()) 
