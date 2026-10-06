"""Поддержка: тикеты игроков."""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from bot.keyboards.main import get_back_menu
from bot.keyboards.support import (
    SupportMenu, get_categories_menu, get_support_menu, get_ticket_actions,
)
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


class SupportState(StatesGroup):
    waiting_subject = State()
    waiting_message = State()
    waiting_reply = State()


@router.callback_query(SupportMenu.filter(F.action == "menu"))
async def cb_support_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    await _render_support_menu(query)


@router.message(Command("support"))
async def cmd_support(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await message.answer("❌ Сначала /start")
            return

        open_count = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.user_id == user.id,
                Ticket.status.in_(["open", "pending"]),
            )
        )).scalar() or 0

    text = (
        f"💬 <b>Поддержка Indy Carts</b>\n\n"
        f"Мы отвечаем в порядке очереди. "
        f"Срочные тикеты обрабатываются быстрее.\n\n"
        f"📋 Открытых тикетов: <b>{open_count}</b>"
    )
    await message.answer(text, reply_markup=get_support_menu(open_count), parse_mode="HTML")


async def _render_support_menu(query: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        open_count = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.user_id == user.id,
                Ticket.status.in_(["open", "pending"]),
            )
        )).scalar() or 0

    text = (
        f"💬 <b>Поддержка Indy Carts</b>\n\n"
        f"Мы отвечаем в порядке очереди. "
        f"Срочные тикеты обрабатываются быстрее.\n\n"
        f"📋 Открытых тикетов: <b>{open_count}</b>"
    )
    await safe_render(query, text, get_support_menu(open_count))


@router.callback_query(SupportMenu.filter(F.action == "new"))
async def cb_new_ticket(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        if user.last_ticket_at:
            cooldown = timedelta(minutes=settings.SUPPORT_TICKET_COOLDOWN_MIN)
            if datetime.utcnow() - user.last_ticket_at < cooldown:
                left = cooldown - (datetime.utcnow() - user.last_ticket_at)
                mins = int(left.total_seconds() // 60) + 1
                await safe_answer(query, f"⏳ Следующий тикет через {mins} мин.", show_alert=True)
                return

        open_count = (await session.execute(
            select(func.count(Ticket.id)).where(
                Ticket.user_id == user.id,
                Ticket.status.in_(["open", "pending"]),
            )
        )).scalar() or 0

        if open_count >= settings.SUPPORT_TICKET_MAX_OPEN:
            await safe_answer(
                query,
                f"❌ Максимум {settings.SUPPORT_TICKET_MAX_OPEN} открытых тикетов",
                show_alert=True,
            )
            return

    await safe_render(
        query,
        "📩 <b>Новый тикет</b>\n\nВыбери категорию:",
        get_categories_menu(),
    )


@router.callback_query(SupportMenu.filter(F.action == "cat"))
async def cb_category(query: CallbackQuery, callback_data: SupportMenu) -> None:
    await safe_answer(query)
    category = callback_data.category

    if category not in TICKET_CATEGORIES:
        return

    priority = "urgent" if category in ("bug", "balance", "cards") else "normal"

    b = InlineKeyboardBuilder()
    b.button(
        text="✅ Продолжить",
        callback_data=SupportMenu(action="subject", category=category).pack(),
    )
    b.button(text="🔙 Назад", callback_data=SupportMenu(action="new").pack())
    b.adjust(1)

    auto_note = ""
    if priority == "urgent":
        auto_note = "\n\n🔴 <i>Эта категория обрабатывается в первую очередь.</i>"

    await safe_render(
        query,
        f"📩 <b>{TICKET_CATEGORIES[category]}</b>{auto_note}\n\n"
        f"Опиши коротко суть проблемы (тема тикета):",
        b.as_markup(),
    )


@router.callback_query(SupportMenu.filter(F.action == "subject"))
async def cb_subject(query: CallbackQuery, callback_data: SupportMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(category=callback_data.category)
    await state.set_state(SupportState.waiting_subject)

    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=SupportMenu(action="menu").pack())

    await safe_render(
        query,
        "✏️ <b>Тема тикета</b>\n\nКоротко опиши проблему (до 128 символов):",
        b.as_markup(),
    )


@router.message(SupportState.waiting_subject)
async def handle_subject(message: Message, state: FSMContext) -> None:
    subject = message.text.strip()[:128]
    if len(subject) < 5:
        await message.answer("❌ Минимум 5 символов")
        return

    await state.update_data(subject=subject)
    await state.set_state(SupportState.waiting_message)

    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=SupportMenu(action="menu").pack())

    await message.answer(
        "📝 <b>Опиши детали</b>\n\n"
        "Чем подробнее — тем быстрее поможем. "
        "Можно приложить скриншот (отправь фото).",
        reply_markup=b.as_markup(),
        parse_mode="HTML",
    )


@router.message(SupportState.waiting_message)
async def handle_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    category = data.get("category")
    subject = data.get("subject")
    await state.clear()

    text = message.text or message.caption or "[без текста]"
    if len(text) < 10:
        await message.answer("❌ Минимум 10 символов")
        return

    now = datetime.utcnow()
    priority = "urgent" if category in ("bug", "balance", "cards") else "normal"

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        ticket = Ticket(
            user_id=user.id,
            subject=subject,
            category=category,
            priority=priority,
            status="open",
        )
        session.add(ticket)
        await session.flush()

        session.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=user.id,
            is_staff=False,
            text=text,
        ))

        user.last_ticket_at = now

        await session.commit()
        ticket_id = ticket.id
        username = user.username

    await message.answer(
        f"✅ <b>Тикет #{ticket_id} создан</b>\n\n"
        f"Категория: {TICKET_CATEGORIES[category]}\n"
        f"Приоритет: {TICKET_PRIORITIES[priority]}\n\n"
        f"Мы ответим в ближайшее время. "
        f"Уведомление придёт автоматически.",
        parse_mode="HTML",
    )

    from core.constants import ROLE_LEVELS
    from db.models import AdminRole

    async with AsyncSessionLocal() as session:
        staff_roles = (await session.execute(
            select(AdminRole).where(AdminRole.is_active == True)
        )).scalars().all()

        for sr in staff_roles:
            if ROLE_LEVELS.get(sr.role, 0) >= ROLE_LEVELS["support"]:
                staff_user = await session.get(User, sr.user_id)
                if staff_user:
                    try:
                        await message.bot.send_message(
                            staff_user.telegram_id,
                            f"📩 <b>Новый тикет #{ticket_id}</b>\n\n"
                            f"От: @{username}\n"
                            f"Категория: {TICKET_CATEGORIES[category]}\n"
                            f"Приоритет: {TICKET_PRIORITIES[priority]}\n"
                            f"Тема: {subject}",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

    logger.info(f"🎫 Тикет #{ticket_id} от @{username} ({category})")


@router.callback_query(SupportMenu.filter(F.action == "my"))
async def cb_my_tickets(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        tickets = (await session.execute(
            select(Ticket)
            .where(Ticket.user_id == user.id)
            .order_by(Ticket.created_at.desc())
            .limit(10)
        )).scalars().all()

    if not tickets:
        b = InlineKeyboardBuilder()
        b.button(text="📩 Создать тикет", callback_data=SupportMenu(action="new").pack())
        b.button(text="🔙 Назад", callback_data=SupportMenu(action="menu").pack())
        b.adjust(1)
        await safe_render(query, "📋 <b>У тебя нет тикетов</b>", b.as_markup())
        return

    b = InlineKeyboardBuilder()
    for t in tickets:
        status = TICKET_STATUSES.get(t.status, "?")
        short = t.subject[:25]
        b.button(
            text=f"{status} #{t.id} · {short}",
            callback_data=SupportMenu(action="view", ticket_id=t.id).pack(),
        )
    b.button(text="📩 Создать тикет", callback_data=SupportMenu(action="new").pack())
    b.button(text="🔙 Назад", callback_data=SupportMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, "📋 <b>Мои тикеты</b>", b.as_markup())


@router.callback_query(SupportMenu.filter(F.action == "view"))
async def cb_view_ticket(query: CallbackQuery, callback_data: SupportMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        ticket = await session.get(Ticket, callback_data.ticket_id)

        if ticket is None or user is None or ticket.user_id != user.id:
            await safe_answer(query, "❌ Тикет не найден", show_alert=True)
            return

        messages = (await session.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.created_at)
            .limit(20)
        )).scalars().all()

    text = (
        f"📩 <b>Тикет #{ticket.id}</b>\n\n"
        f"📌 {ticket.subject}\n"
        f"🏷 {TICKET_CATEGORIES.get(ticket.category, '?')}\n"
        f"⚡ {TICKET_PRIORITIES.get(ticket.priority, '?')}\n"
        f"📊 {TICKET_STATUSES.get(ticket.status, '?')}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )

    for m in messages:
        who = "🛡" if m.is_staff else "👤"
        text += f"{who} <b>{'Саппорт' if m.is_staff else 'Ты'}:</b>\n{m.text[:400]}\n\n"

    can_close = ticket.status in ("open", "pending")

    await safe_render(
        query, text,
        get_ticket_actions(ticket.id, is_owner=can_close),
    )


@router.callback_query(SupportMenu.filter(F.action == "reply"))
async def cb_reply(query: CallbackQuery, callback_data: SupportMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(reply_ticket_id=callback_data.ticket_id)
    await state.set_state(SupportState.waiting_reply)

    b = InlineKeyboardBuilder()
    b.button(
        text="❌ Отмена",
        callback_data=SupportMenu(action="view", ticket_id=callback_data.ticket_id).pack(),
    )

    await safe_render(query, "✍️ <b>Ответ в тикет</b>\n\nНапиши сообщение:", b.as_markup())


@router.message(SupportState.waiting_reply)
async def handle_reply(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    await state.clear()

    text = message.text or message.caption or ""
    if len(text) < 2:
        await message.answer("❌ Слишком коротко")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        ticket = await session.get(Ticket, ticket_id)

        if ticket is None or user is None or ticket.user_id != user.id:
            await message.answer("❌ Тикет не найден")
            return

        if ticket.status == "closed":
            await message.answer("❌ Тикет закрыт")
            return

        session.add(TicketMessage(
            ticket_id=ticket.id,
            sender_id=user.id,
            is_staff=False,
            text=text,
        ))

        if ticket.status == "pending":
            ticket.status = "open"

        await session.commit()

    await message.answer(f"✅ Ответ добавлен в тикет #{ticket_id}")


@router.callback_query(SupportMenu.filter(F.action == "close"))
async def cb_close_ticket(query: CallbackQuery, callback_data: SupportMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        ticket = await session.get(Ticket, callback_data.ticket_id)

        if ticket is None or user is None or ticket.user_id != user.id:
            await safe_answer(query, "❌ Тикет не найден", show_alert=True)
            return

        ticket.status = "closed"
        ticket.closed_at = datetime.utcnow()
        ticket.closed_by = user.id

        await session.commit()

    await safe_render(query, f"🔒 <b>Тикет #{ticket.id} закрыт</b>", get_back_menu())


@router.callback_query(SupportMenu.filter(F.action == "faq"))
async def cb_faq(query: CallbackQuery) -> None:
    await safe_answer(query)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=SupportMenu(action="menu").pack())

    await safe_render(
        query,
        "📖 <b>FAQ Indy Carts</b>\n\n"
        "Прежде чем создавать тикет, проверь:\n\n"
        "💰 <b>Баланс / монеты</b>\n"
        "Проверь историю в /profile\n\n"
        "🃏 <b>Пропала карта</b>\n"
        "Проверь коллекцию — может быть в PvP-стаке\n\n"
        "⚔️ <b>PvP не работает</b>\n"
        "Проверь бан: /bank → FAQ\n\n"
        "💎 <b>Indy+ не работает</b>\n"
        "Проверь /plus — там срок подписки\n\n"
        "🏦 <b>Кредит</b>\n"
        "Вся история в /bank → 📜 История\n\n"
        "❓ <b>Не нашёл ответа?</b>\n"
        "Создай тикет — разберёмся.",
        b.as_markup(),
) 
