"""Панель саппорта — для ролей support+."""

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from bot.keyboards.support import get_staff_ticket_actions
from bot.utils.decorators import check_role
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    TICKET_CATEGORIES, TICKET_PRIORITIES, TICKET_STATUSES,
)
from core.logger import setup_logger
from db.models import Ticket, TicketMessage, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


class SupportPanel(CallbackData, prefix="support_panel"):
    action: str
    ticket_id: int = 0
    filter: str = ""


class StaffReplyState(StatesGroup):
    waiting_text = State()


@router.message(Command("support_panel"))
async def cmd_support_panel(message: Message) -> None:
    if not await check_role(message.from_user.id, "support"):
        await message.answer("⛔ Нет доступа")
        return
    await _show_panel(message, is_message=True)


@router.callback_query(SupportPanel.filter(F.action == "refresh"))
async def cb_refresh(query: CallbackQuery) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)
    await _show_panel(query)


async def _show_panel(target, is_message: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        open_count = (await session.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "open")
        )).scalar() or 0

        pending_count = (await session.execute(
            select(func.count(Ticket.id)).where(Ticket.status == "pending")
        )).scalar() or 0

        urgent_count = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status.in_(["open", "pending"]),
                Ticket.priority == "urgent",
            )
        )).scalar() or 0

        day_ago = datetime.utcnow().replace(hour=0, minute=0, second=0)
        resolved_today = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status.in_(["resolved", "closed"]),
                Ticket.closed_at > day_ago,
            )
        )).scalar() or 0

    text = (
        f"🛡 <b>Панель поддержки</b>\n\n"
        f"📬 Открытых: <b>{open_count}</b>\n"
        f"⏳ В ожидании: <b>{pending_count}</b>\n"
        f"🔴 Срочных: <b>{urgent_count}</b>\n"
        f"✅ Решено сегодня: <b>{resolved_today}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Быстрые действия:</b>"
    )

    b = InlineKeyboardBuilder()
    b.button(text=f"📬 Открытые ({open_count})", callback_data=SupportPanel(action="list", filter="open").pack())
    b.button(text=f"🔴 Срочные ({urgent_count})", callback_data=SupportPanel(action="list", filter="urgent").pack())
    b.button(text=f"⏳ Ожидают ({pending_count})", callback_data=SupportPanel(action="list", filter="pending").pack())
    b.button(text="👤 Мои тикеты", callback_data=SupportPanel(action="list", filter="mine").pack())
    b.button(text="📊 Статистика", callback_data=SupportPanel(action="stats").pack())
    b.button(text="🔄 Обновить", callback_data=SupportPanel(action="refresh").pack())
    b.adjust(2, 2, 1, 1)

    if is_message:
        await target.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")
    else:
        await safe_render(target, text, b.as_markup())


@router.callback_query(SupportPanel.filter(F.action == "list"))
async def cb_list(query: CallbackQuery, callback_data: SupportPanel) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)

    filter_type = callback_data.filter

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        stmt = select(Ticket)

        if filter_type == "open":
            stmt = stmt.where(Ticket.status == "open")
        elif filter_type == "pending":
            stmt = stmt.where(Ticket.status == "pending")
        elif filter_type == "urgent":
            stmt = stmt.where(
                Ticket.status.in_(["open", "pending"]),
                Ticket.priority == "urgent",
            )
        elif filter_type == "mine" and user:
            stmt = stmt.where(Ticket.assigned_to == user.id)

        tickets = (await session.execute(
            stmt.order_by(
                Ticket.priority.desc(),
                Ticket.created_at.asc(),
            ).limit(15)
        )).scalars().all()

        usernames = {}
        for t in tickets:
            if t.user_id not in usernames:
                u = await session.get(User, t.user_id)
                if u:
                    usernames[t.user_id] = u.username

    if not tickets:
        b = InlineKeyboardBuilder()
        b.button(text="🔙 К панели", callback_data=SupportPanel(action="refresh").pack())
        b.adjust(1)
        await safe_render(query, "✅ <b>Тикетов нет</b>", b.as_markup())
        return

    title_map = {
        "open": "📬 Открытые",
        "pending": "⏳ В ожидании",
        "urgent": "🔴 Срочные",
        "mine": "👤 Мои",
    }

    text = f"<b>{title_map.get(filter_type, 'Тикеты')}</b>\n\n"

    b = InlineKeyboardBuilder()
    for t in tickets:
        uname = usernames.get(t.user_id, "?")
        priority_emoji = "🔴" if t.priority == "urgent" else (
            "🟠" if t.priority == "high" else "🟡"
        )
        short = t.subject[:30]
        b.button(
            text=f"{priority_emoji} #{t.id} @{uname} · {short}",
            callback_data=SupportPanel(action="view", ticket_id=t.id).pack(),
        )
    b.button(text="🔙 К панели", callback_data=SupportPanel(action="refresh").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(SupportPanel.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: SupportPanel) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        ticket = await session.get(Ticket, callback_data.ticket_id)
        if ticket is None:
            await safe_answer(query, "❌ Тикет не найден", show_alert=True)
            return

        user = await session.get(User, ticket.user_id)
        messages = (await session.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.created_at)
            .limit(30)
        )).scalars().all()

        user_info = ""
        if user:
            user_info = (
                f"👤 @{user.username}\n"
                f"💰 {user.balance:,}\n"
                f"⚔️ {user.pvp_rating} PvP\n"
                f"💎 {'Indy+' if user.plus_tier == 'indy_plus' else 'free'}\n"
                f"🚫 {user.ban_level}\n"
                f"📊 Trust: {user.trust_score}"
            )

    text = (
        f"📩 <b>Тикет #{ticket.id}</b>\n\n"
        f"📌 {ticket.subject}\n"
        f"🏷 {TICKET_CATEGORIES.get(ticket.category, '?')}\n"
        f"⚡ {TICKET_PRIORITIES.get(ticket.priority, '?')}\n"
        f"📊 {TICKET_STATUSES.get(ticket.status, '?')}\n"
        f"📅 {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"━━━ <b>О игроке</b> ━━━\n"
        f"{user_info}\n\n"
        f"━━━ <b>Переписка</b> ━━━\n\n"
    )

    for m in messages[-5:]:
        who = "🛡 Саппорт" if m.is_staff else "👤 Игрок"
        text += f"<b>{who}:</b>\n{m.text[:300]}\n\n"

    await safe_render(query, text, get_staff_ticket_actions(ticket.id))


@router.callback_query(SupportPanel.filter(F.action == "reply"))
async def cb_staff_reply(query: CallbackQuery, callback_data: SupportPanel, state: FSMContext) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)
    await state.update_data(staff_ticket_id=callback_data.ticket_id)
    await state.set_state(StaffReplyState.waiting_text)

    b = InlineKeyboardBuilder()
    b.button(
        text="❌ Отмена",
        callback_data=SupportPanel(action="view", ticket_id=callback_data.ticket_id).pack(),
    )
    b.adjust(1)

    await safe_render(query, "✍️ <b>Ответ игроку</b>\n\nНапиши сообщение:", b.as_markup())


@router.message(StaffReplyState.waiting_text)
async def handle_staff_reply(message: Message, state: FSMContext) -> None:
    if not await check_role(message.from_user.id, "support"):
        await message.answer("⛔ Нет доступа")
        return

    data = await state.get_data()
    ticket_id = data.get("staff_ticket_id")
    await state.clear()

    text = message.text or message.caption or ""
    if len(text) < 2:
        await message.answer("❌ Слишком коротко")
        return

    async with AsyncSessionLocal() as session:
        staff = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        ticket = await session.get(Ticket, ticket_id)

        if ticket is None or staff is None:
            await message.answer("❌ Тикет не найден")
            return

        if ticket.status in ("resolved", "closed"):
            await message.answer("❌ Тикет уже закрыт")
            return

        session.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=staff.id,
            is_staff=True,
            text=text,
        ))

        if ticket.assigned_to is None:
            ticket.assigned_to = staff.id

        if ticket.status == "pending":
            ticket.status = "open"

        await session.commit()

        ticket_user = await session.get(User, ticket.user_id)
        if ticket_user:
            try:
                await message.bot.send_message(
                    ticket_user.telegram_id,
                    f"📩 <b>Ответ в тикете #{ticket.id}</b>\n\n"
                    f"🛡 <b>Поддержка:</b>\n{text}\n\n"
                    f"Ответить: /support",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    await message.answer(f"✅ Ответ отправлен в тикет #{ticket_id}")


@router.callback_query(SupportPanel.filter(F.action == "resolve"))
async def cb_resolve(query: CallbackQuery, callback_data: SupportPanel) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)
    await _resolve_ticket(query, callback_data.ticket_id, "resolved")


@router.callback_query(SupportPanel.filter(F.action == "close"))
async def cb_close(query: CallbackQuery, callback_data: SupportPanel) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)
    await _resolve_ticket(query, callback_data.ticket_id, "closed")


@router.callback_query(SupportPanel.filter(F.action == "urgent"))
async def cb_urgent(query: CallbackQuery, callback_data: SupportPanel) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        ticket = await session.get(Ticket, callback_data.ticket_id)
        if ticket:
            ticket.priority = "urgent"
            await session.commit()

    await safe_render(query, f"🚨 Тикет #{callback_data.ticket_id} — срочный")


async def _resolve_ticket(query: CallbackQuery, ticket_id: int, new_status: str) -> None:
    async with AsyncSessionLocal() as session:
        staff = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        ticket = await session.get(Ticket, ticket_id)
        if ticket is None or staff is None:
            return

        ticket.status = new_status
        ticket.closed_at = datetime.utcnow()
        ticket.closed_by = staff.id

        if new_status == "resolved":
            staff.tickets_resolved += 1
            staff.support_reputation += settings.SUPPORT_REPUTATION_PER_RESOLVE

        await session.commit()

        ticket_user = await session.get(User, ticket.user_id)
        if ticket_user:
            emoji = "✅" if new_status == "resolved" else "🔒"
            try:
                await query.bot.send_message(
                    ticket_user.telegram_id,
                    f"{emoji} <b>Тикет #{ticket.id} "
                    f"{'решён' if new_status == 'resolved' else 'закрыт'}</b>\n\n"
                    f"Спасибо за обращение!",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    b = InlineKeyboardBuilder()
    b.button(text="🔙 К панели", callback_data=SupportPanel(action="refresh").pack())
    b.adjust(1)
    await safe_render(query, f"✅ Тикет #{ticket_id} обработан", b.as_markup())


@router.callback_query(SupportPanel.filter(F.action == "stats"))
async def cb_stats(query: CallbackQuery) -> None:
    if not await check_role(query.from_user.id, "support"):
        await safe_answer(query, "⛔ Нет доступа", show_alert=True)
        return
    await safe_answer(query)

    day_ago = datetime.utcnow().replace(hour=0, minute=0, second=0)

    async with AsyncSessionLocal() as session:
        total = (await session.execute(
            select(func.count(Ticket.id))
        )).scalar() or 0

        resolved_today = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.status.in_(["resolved", "closed"]),
                Ticket.closed_at > day_ago,
            )
        )).scalar() or 0

        top = (await session.execute(
            select(User)
            .where(User.tickets_resolved > 0)
            .order_by(User.tickets_resolved.desc())
            .limit(5)
        )).scalars().all()

    text = (
        f"📊 <b>Статистика поддержки</b>\n\n"
        f"📋 Всего тикетов: <b>{total}</b>\n"
        f"✅ Решено сегодня: <b>{resolved_today}</b>\n\n"
        f"<b>🏆 Топ саппортов:</b>\n"
    )

    for i, u in enumerate(top, 1):
        text += f"{i}. @{u.username} — {u.tickets_resolved}\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 К панели", callback_data=SupportPanel(action="refresh").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup()) 
