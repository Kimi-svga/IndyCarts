"""Кланы: создание, вступление, вклад, управление, топ, приглашения."""

from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.clan import (
    ClanMenu, get_clan_menu, get_clan_view, get_create_cancel,
    get_create_confirm, get_deposit_menu, get_disband_confirm,
    get_invite_actions, get_invite_cancel, get_invites_menu,
    get_kick_confirm, get_leave_confirm, get_manage_menu,
    get_member_actions, get_no_clan_menu, get_outgoing_menu,
    get_search_cancel, get_search_results, get_skip_desc, get_top_nav,
)
from bot.keyboards.main import MainMenu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    CLAN_MAX_LEVEL, CLAN_ROLE_EMOJI, CLAN_ROLE_NAMES,
)
from core.logger import setup_logger
from db.models import Clan, ClanInvite, ClanMember, User
from db.session import AsyncSessionLocal
from services import clan as clan_service
from services.clan import (
    accept_invite, create_clan, create_invite, decline_invite,
    deposit, get_clan_bonuses, get_clan_log, get_clan_member_count,
    get_clan_members, get_clan_pending_invites, get_clan_rating,
    get_pending_invites, get_top_clans, get_user_clan,
    get_xp_for_next_level, join_clan, kick_member, leave_clan,
    search_clans, set_role,
)

router = Router()
logger = setup_logger()

MEMBERS_PER_PAGE = 10


# ═════════════════════════════════════════════
# FSM STATE
# ═════════════════════════════════════════════

class ClanState(StatesGroup):
    """FSM создания клана + ввод юзернейма + кастомный вклад."""
    waiting_name = State()
    waiting_tag = State()
    waiting_desc = State()
    waiting_search = State()
    waiting_invite_username = State()
    waiting_deposit_amount = State()


# ═════════════════════════════════════════════
# ХЕЛПЕРЫ
# ═════════════════════════════════════════════

async def _get_db_user(session, telegram_id: int) -> User | None:
    return (await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )).scalar_one_or_none()


def _render_clan_header(clan: Clan, member: ClanMember, count: int) -> str:
    """Шапка экрана клана."""
    emoji = CLAN_ROLE_EMOJI.get(member.role, "👤")
    role = CLAN_ROLE_NAMES.get(member.role, member.role)
    bonuses = get_clan_bonuses(clan.level)
    next_xp = get_xp_for_next_level(clan.level)

    xp_line = "🏆 <b>МАКСИМАЛЬНЫЙ УРОВЕНЬ</b>"
    if next_xp > 0:
        left = max(0, next_xp - clan.xp)
        xp_line = f"📈 До ур.{clan.level + 1}: <b>{left:,}</b> XP"

    desc_line = f"\n📝 {clan.description}" if clan.description else ""

    return (
        f"🏰 <b>[{clan.tag}] {clan.name}</b>{desc_line}\n\n"
        f"👑 Уровень: <b>{clan.level}</b>/{CLAN_MAX_LEVEL}\n"
        f"📊 XP: <b>{clan.xp:,}</b>\n"
        f"💰 Казна: <b>{clan.treasury:,}</b>\n"
        f"👥 Участники: <b>{count}</b>/{bonuses.max_members}\n"
        f"{xp_line}\n\n"
        f"<b>Твоя роль:</b> {emoji} {role}\n"
        f"<b>Твой вклад:</b> <b>{member.contribution:,}</b>\n\n"
        f"<b>Бонусы клана:</b>\n"
        f"🍀 Дроп: +{bonuses.drop_bonus * 100:.0f}%\n"
        f"💰 Монеты: +{bonuses.money_bonus * 100:.0f}%\n"
        f"🎯 Аукцион: −{bonuses.auction_discount:.1f}%\n"
        f"🎴 Доп. попытки: +{bonuses.extra_attempts}"
    )


# ═════════════════════════════════════════════
# ГЛАВНЫЙ ЭКРАН
# ═════════════════════════════════════════════

@router.callback_query(MainMenu.filter(F.action == "clans"))
async def cb_clans(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        clan, member = await get_user_clan(session, user.id)

        if clan is None or member is None:
            pending = await get_pending_invites(session, user.id)
            invites_line = ""
            if pending:
                invites_line = f"\n\n📨 <b>Приглашений: {len(pending)}</b>"

            text = (
                f"🏰 <b>Кланы</b>\n\n"
                f"Кланы — это объединения игроков.\n"
                f"Вместе вы прокачиваете уровень, получаете бонусы,\n"
                f"и поднимаетесь в топ.{invites_line}\n\n"
                f"<b>Создание клана:</b>\n"
                f"💰 <b>{settings.CLAN_CREATE_PRICE:,}</b> монет\n"
                f"💎 <b>Бесплатно</b> для Indy+\n\n"
                f"<b>Бонусы кланов:</b>\n"
                f"🍀 Больше дропа\n"
                f"💰 Больше монет\n"
                f"🎯 Меньше комиссия аукциона\n"
                f"🎴 Доп. попытки"
            )
            await safe_render(query, text, get_no_clan_menu())
            return

        count = await get_clan_member_count(session, clan.id)
        pending_out = await get_clan_pending_invites(session, clan.id)

    text = _render_clan_header(clan, member, count)

    await safe_render(
        query, text,
        get_clan_menu(member.role, has_incoming_invites=bool(pending_out)),
    )


@router.callback_query(ClanMenu.filter(F.action == "menu"))
async def cb_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    await cb_clans(query)


# ═════════════════════════════════════════════
# СОЗДАНИЕ КЛАНА (FSM)
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "create_start"))
async def cb_create_start(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return

        clan, _ = await get_user_clan(session, user.id)
        if clan is not None:
            await safe_render(query, "❌ Ты уже в клане", get_no_clan_menu())
            return

        is_free = clan_service.is_plus_active(user)
        price = settings.CLAN_CREATE_PRICE

        if not is_free and user.balance < price:
            await safe_render(
                query,
                f"❌ <b>Недостаточно монет</b>\n\n"
                f"Нужно: <b>{price:,}</b>\n"
                f"У тебя: <b>{user.balance:,}</b>\n\n"
                f"💎 Или оформи Indy+ — создание бесплатно.",
                get_no_clan_menu(),
            )
            return

        price_line = (
            "💎 <b>Бесплатно</b> (у тебя активен Indy+)"
            if is_free else
            f"💰 Стоимость: <b>{price:,}</b>"
        )

    await state.set_state(ClanState.waiting_name)
    await safe_render(
        query,
        f"🏰 <b>Создание клана</b>\n\n"
        f"{price_line}\n\n"
        f"<b>Шаг 1/3 — Название</b>\n"
        f"Введи название клана (3–24 символа):",
        get_create_cancel(),
    )


@router.message(ClanState.waiting_name, F.text)
async def handle_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not (3 <= len(name) <= 24):
        await message.answer("❌ Название: 3–24 символа")
        return

    await state.update_data(name=name)
    await state.set_state(ClanState.waiting_tag)
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        f"<b>Шаг 2/3 — Тег</b>\n"
        f"Введи тег клана (2–4 заглавные буквы, например: <code>FST</code>):",
        parse_mode="HTML",
    )


@router.message(ClanState.waiting_tag, F.text)
async def handle_tag(message: Message, state: FSMContext) -> None:
    tag = message.text.strip().upper()
    if not (2 <= len(tag) <= 4) or not tag.isalpha():
        await message.answer("❌ Тег: 2–4 буквы (A-Z)")
        return

    await state.update_data(tag=tag)
    await state.set_state(ClanState.waiting_desc)
    await message.answer(
        f"✅ Тег: <b>[{tag}]</b>\n\n"
        f"<b>Шаг 3/3 — Описание</b>\n"
        f"Напиши описание клана (до 200 символов)\n"
        f"или нажми «Пропустить»:",
        reply_markup=get_skip_desc(),
        parse_mode="HTML",
    )


@router.message(ClanState.waiting_desc, F.text)
async def handle_desc(message: Message, state: FSMContext) -> None:
    desc = message.text.strip()[:200]
    await state.update_data(description=desc or None)
    await _show_create_confirm(message, state)


@router.callback_query(ClanMenu.filter(F.action == "create_skip_desc"))
async def cb_skip_desc(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(description=None)
    await _show_create_confirm(query, state)


async def _show_create_confirm(target, state: FSMContext) -> None:
    data = await state.get_data()
    name = data.get("name", "?")
    tag = data.get("tag", "?")
    desc = data.get("description") or "—"

    text = (
        f"🏰 <b>Проверь данные</b>\n\n"
        f"<b>Название:</b> {name}\n"
        f"<b>Тег:</b> [{tag}]\n"
        f"<b>Описание:</b> {desc}\n\n"
        f"Создать клан?"
    )

    if isinstance(target, CallbackQuery):
        await safe_render(target, text, get_create_confirm())
    else:
        await target.answer(text, reply_markup=get_create_confirm(), parse_mode="HTML")


@router.callback_query(ClanMenu.filter(F.action == "create_confirm"))
async def cb_create_confirm(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)

    data = await state.get_data()
    name = data.get("name")
    tag = data.get("tag")
    description = data.get("description")
    await state.clear()

    if not name or not tag:
        await safe_render(query, "❌ Данные потеряны. Начни заново.", get_no_clan_menu())
        return

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return

        result = await create_clan(session, user, name, tag, description)

    if not result.ok:
        await safe_render(query, f"❌ {result.reason}", get_no_clan_menu())
        return

    free = (result.data or {}).get("free", False)

    text = (
        f"🎉 <b>Клан создан!</b>\n\n"
        f"🏰 <b>[{tag}] {name}</b>\n\n"
        f"{'💎 Создано бесплатно (Indy+)' if free else f'💰 Потрачено: {settings.CLAN_CREATE_PRICE:,}'}\n\n"
        f"Теперь приглашай друзей и копи казну!"
    )

    await safe_render(query, text, get_clan_menu("leader"))


# ═════════════════════════════════════════════
# ПОИСК
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "search"))
async def cb_search(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(ClanState.waiting_search)

    await safe_render(
        query,
        "🔍 <b>Поиск кланов</b>\n\n"
        "Введи название или тег:",
        get_search_cancel(),
    )


@router.message(ClanState.waiting_search, F.text)
async def handle_search(message: Message, state: FSMContext) -> None:
    query_text = message.text.strip()
    await state.clear()

    if len(query_text) < 2:
        await message.answer("❌ Минимум 2 символа")
        return

    async with AsyncSessionLocal() as session:
        clans = await search_clans(session, query_text, limit=10)

    if not clans:
        await message.answer(
            f"❌ Ничего не найдено по «{query_text}»",
            reply_markup=get_search_cancel(),
        )
        return

    await message.answer(
        f"🔍 Найдено: <b>{len(clans)}</b>",
        reply_markup=get_search_results(clans),
        parse_mode="HTML",
    )


# ═════════════════════════════════════════════
# ПРОСМОТР ЧУЖОГО КЛАНА
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        clan = await session.get(Clan, callback_data.clan_id)
        if clan is None or not clan.is_active:
            await safe_render(query, "❌ Клан недоступен", get_no_clan_menu())
            return

        count = await get_clan_member_count(session, clan.id)
        rating = await get_clan_rating(session, clan.id)

        user = await _get_db_user(session, query.from_user.id)
        already_in_clan = False
        if user:
            my_clan, _ = await get_user_clan(session, user.id)
            already_in_clan = my_clan is not None

    bonuses = get_clan_bonuses(clan.level)
    desc_line = f"\n📝 {clan.description}" if clan.description else ""
    open_line = "🔓 Открыт для вступления" if clan.is_open else "🔒 Только по приглашению"

    text = (
        f"🏰 <b>[{clan.tag}] {clan.name}</b>{desc_line}\n\n"
        f"👑 Уровень: <b>{clan.level}</b>/{CLAN_MAX_LEVEL}\n"
        f"👥 Участники: <b>{count}</b>/{bonuses.max_members}\n"
        f"💰 Казна: <b>{clan.treasury:,}</b>\n"
        f"🏆 Рейтинг: <b>{rating:,}</b>\n\n"
        f"{open_line}\n\n"
        f"<b>Бонусы:</b>\n"
        f"🍀 Дроп: +{bonuses.drop_bonus * 100:.0f}%\n"
        f"💰 Монеты: +{bonuses.money_bonus * 100:.0f}%\n"
        f"🎯 Аукцион: −{bonuses.auction_discount:.1f}%\n"
        f"🎴 Попытки: +{bonuses.extra_attempts}"
    )

    await safe_render(
        query, text,
        get_clan_view(clan.id, clan.is_open, already_in_clan),
    )


@router.callback_query(ClanMenu.filter(F.action == "join"))
async def cb_join(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return

        result = await join_clan(session, user, callback_data.clan_id)

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    await cb_clans(query)


# ═════════════════════════════════════════════
# УЧАСТНИКИ
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "members"))
async def cb_members(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return

        clan, my_member = await get_user_clan(session, user.id)
        if clan is None or my_member is None:
            await safe_render(query, "❌ Ты не в клане", get_no_clan_menu())
            return

        all_members = await get_clan_members(session, clan.id, limit=100)

    total = len(all_members)
    total_pages = max(1, (total + MEMBERS_PER_PAGE - 1) // MEMBERS_PER_PAGE)
    index = max(0, min(callback_data.index, total_pages - 1))

    start = index * MEMBERS_PER_PAGE
    end = start + MEMBERS_PER_PAGE
    page = all_members[start:end]

    text = f"👥 <b>Участники [{clan.tag}]</b> ({total})\n\n"

    b = InlineKeyboardBuilder()
    for m, u in page:
        emoji = CLAN_ROLE_EMOJI.get(m.role, "👤")
        b.button(
            text=f"{emoji} @{u.username} · вклад {m.contribution:,}",
            callback_data=ClanMenu(action="member_view", member_id=u.id).pack(),
        )
    b.adjust(1)

    if index > 0:
        b.button(
            text="⬅️",
            callback_data=ClanMenu(action="members", clan_id=clan.id, index=index - 1).pack(),
        )
    b.button(text=f"{index + 1}/{total_pages}", callback_data="noop")
    if index < total_pages - 1:
        b.button(
            text="➡️",
            callback_data=ClanMenu(action="members", clan_id=clan.id, index=index + 1).pack(),
        )
    b.button(text="🔙 К клану", callback_data=ClanMenu(action="menu").pack())

    await safe_render(query, text, b.as_markup())


@router.callback_query(ClanMenu.filter(F.action == "member_view"))
async def cb_member_view(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = await _get_db_user(session, query.from_user.id)
        if me is None:
            return

        target = await session.get(User, callback_data.member_id)
        if target is None:
            await safe_render(query, "❌ Игрок не найден", get_clan_menu("member"))
            return

        clan, my_member = await get_user_clan(session, me.id)
        if clan is None or my_member is None:
            return

        target_member = await clan_service.get_clan_member_by_user(
            session, clan.id, target.id,
        )
        if target_member is None:
            await safe_render(query, "❌ Игрок не в твоём клане", get_clan_menu(my_member.role))
            return

    emoji = CLAN_ROLE_EMOJI.get(target_member.role, "👤")
    role_name = CLAN_ROLE_NAMES.get(target_member.role, target_member.role)

    text = (
        f"👤 <b>@{target.username}</b>\n\n"
        f"{emoji} <b>{role_name}</b>\n"
        f"💰 Вклад: <b>{target_member.contribution:,}</b>\n"
        f"⚔️ PvP: <b>{target.pvp_rating}</b>\n"
        f"📅 В клане с: {target_member.joined_at.strftime('%d.%m.%Y')}"
    )

    await safe_render(
        query, text,
        get_member_actions(target.id, target_member.role, my_member.role),
    )


@router.callback_query(ClanMenu.filter(F.action == "kick_confirm"))
async def cb_kick_confirm(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "⚠️ <b>Исключить участника?</b>\n\n"
        "Его вклад в казну останется, но он потеряет доступ.",
        get_kick_confirm(callback_data.member_id),
    )


@router.callback_query(ClanMenu.filter(F.action == "kick"))
async def cb_kick(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await kick_member(session, user, callback_data.member_id)

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    await cb_members(query, ClanMenu(action="members", index=0))


@router.callback_query(ClanMenu.filter(F.action == "promote"))
async def cb_promote(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await set_role(session, user, callback_data.member_id, "officer")

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    await cb_member_view(query, callback_data)


@router.callback_query(ClanMenu.filter(F.action == "demote"))
async def cb_demote(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await set_role(session, user, callback_data.member_id, "member")

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    await cb_member_view(query, callback_data)


# ═════════════════════════════════════════════
# ВКЛАД
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "deposit"))
async def cb_deposit(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None:
            await safe_render(query, "❌ Ты не в клане", get_no_clan_menu())
            return
        balance = user.balance

    await safe_render(
        query,
        f"💰 <b>Вклад в казну</b>\n\n"
        f"Твой баланс: <b>{balance:,}</b>\n"
        f"Минимум вклада: <b>100</b>\n\n"
        f"Каждая монета идёт и в казну, и в XP клана.\n"
        f"Выбери сумму:",
        get_deposit_menu(),
    )


@router.callback_query(ClanMenu.filter(F.action == "deposit_go"))
async def cb_deposit_go(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)
    amount = callback_data.index

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await deposit(session, user, amount)

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    data = result.data or {}
    leveled_up = data.get("leveled_up", False)

    text = f"✅ <b>Внесено: {amount:,}</b>\n"
    text += f"💰 Казна: <b>{data.get('treasury', 0):,}</b>\n"
    text += f"📊 XP клана: <b>{data.get('xp', 0):,}</b>\n"

    if leveled_up:
        text += f"\n🎉 <b>КЛАН ДОСТИГ УРОВНЯ {data.get('new_level')}!</b>"

    await safe_render(query, text, get_clan_menu("member"))


@router.callback_query(ClanMenu.filter(F.action == "deposit_custom"))
async def cb_deposit_custom(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(ClanState.waiting_deposit_amount)

    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="deposit").pack())

    await safe_render(
        query,
        "✏️ Введи сумму вклада (минимум 100):",
        b.as_markup(),
    )


@router.message(ClanState.waiting_deposit_amount, F.text)
async def handle_deposit_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        if amount < 100:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи число ≥ 100")
        return

    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, message.from_user.id)
        if user is None:
            return
        result = await deposit(session, user, amount)

    if not result.ok:
        await message.answer(f"❌ {result.reason}")
        return

    data = result.data or {}
    text = (
        f"✅ <b>Внесено: {amount:,}</b>\n"
        f"💰 Казна: <b>{data.get('treasury', 0):,}</b>\n"
        f"📊 XP: <b>{data.get('xp', 0):,}</b>"
    )
    if data.get("leveled_up"):
        text += f"\n\n🎉 <b>НОВЫЙ УРОВЕНЬ: {data.get('new_level')}!</b>"

    await message.answer(text, parse_mode="HTML")


# ═════════════════════════════════════════════
# ИСТОРИЯ / СТАТИСТИКА
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "log"))
async def cb_log(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None:
            return
        logs = await get_clan_log(session, clan.id, limit=15)

    if not logs:
        await safe_render(query, "📜 История пуста", get_clan_menu(member.role))
        return

    text = "📜 <b>Последние события клана</b>\n\n"
    for log, u in logs:
        who = f"@{u.username}" if u else "система"
        when = log.created_at.strftime("%d.%m %H:%M")
        if log.action == "deposit":
            text += f"💰 {who} внёс {log.amount:,} · {when}\n"
        elif log.action == "join":
            text += f"📥 {who} вступил · {when}\n"
        elif log.action == "leave":
            text += f"📤 {who} вышел · {when}\n"
        elif log.action == "kick":
            text += f"🚪 {who} исключён · {when}\n"
        elif log.action == "level_up":
            text += f"🎉 Клан → ур.{log.amount} · {when}\n"
        elif log.action == "create":
            text += f"🏰 Клан создан · {when}\n"
        elif log.action == "promote":
            text += f"⬆️ {who} → офицер · {when}\n"
        elif log.action == "demote":
            text += f"⬇️ {who} → участник · {when}\n"
        elif log.action == "disband":
            text += f"💥 Клан распущен · {when}\n"
        else:
            text += f"• {log.action} {log.amount} · {when}\n"

    await safe_render(query, text, get_clan_menu(member.role))


@router.callback_query(ClanMenu.filter(F.action == "stats"))
async def cb_stats(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None:
            return

        rating = await get_clan_rating(session, clan.id)
        members = await get_clan_members(session, clan.id, limit=100)

    total_contribution = sum(m.contribution for m, _ in members)
    avg_pvp = (
        sum(u.pvp_rating for _, u in members) // len(members)
        if members else 0
    )

    next_xp = get_xp_for_next_level(clan.level)
    progress_line = "🏆 МАКСИМУМ" if next_xp == 0 else f"{clan.xp:,} / {next_xp:,}"

    text = (
        f"📊 <b>Статистика [{clan.tag}]</b>\n\n"
        f"👑 Уровень: <b>{clan.level}</b>/{CLAN_MAX_LEVEL}\n"
        f"📈 Прогресс: <b>{progress_line}</b>\n"
        f"💰 Казна: <b>{clan.treasury:,}</b>\n"
        f"🏆 Рейтинг: <b>{rating:,}</b>\n\n"
        f"👥 Участников: <b>{len(members)}</b>\n"
        f"💎 Общий вклад: <b>{total_contribution:,}</b>\n"
        f"⚔️ Средний PvP: <b>{avg_pvp}</b>"
    )

    await safe_render(query, text, get_clan_menu(member.role))


# ═════════════════════════════════════════════
# УПРАВЛЕНИЕ
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "manage"))
async def cb_manage(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member.role != "leader":
            await safe_answer(query, "⛔ Только лидер", show_alert=True)
            return

    await safe_render(query, "⚙️ <b>Управление кланом</b>", get_manage_menu())


@router.callback_query(ClanMenu.filter(F.action == "toggle_open"))
async def cb_toggle_open(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member.role != "leader":
            await safe_answer(query, "⛔ Только лидер", show_alert=True)
            return

        clan.is_open = not clan.is_open
        is_open = clan.is_open
        await session.commit()

    status = "🔓 открыт для вступления" if is_open else "🔒 только по приглашению"
    await safe_answer(query, f"Клан теперь {status}", show_alert=True)
    await cb_manage(query)


@router.callback_query(ClanMenu.filter(F.action == "edit_desc"))
async def cb_edit_desc(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member.role != "leader":
            await safe_answer(query, "⛔ Только лидер", show_alert=True)
            return

    await state.set_state(ClanState.waiting_desc)

    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="manage").pack())

    await safe_render(query, "📝 Введи новое описание клана (до 200):", b.as_markup())


@router.message(ClanState.waiting_desc, F.text)
async def handle_edit_desc(message: Message, state: FSMContext) -> None:
    """Обновление описания — перехватывает ClanState.waiting_desc."""
    # Внимание: конфликт с созданием. Решаем по наличию данных FSM.
    data = await state.get_data()
    name = data.get("name")
    tag = data.get("tag")

    if name and tag:
        # Это создание клана
        desc = message.text.strip()[:200]
        await state.update_data(description=desc or None)
        await _show_create_confirm(message, state)
        return

    # Это редактирование описания
    desc = message.text.strip()[:200]
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, message.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member.role != "leader":
            return
        clan.description = desc or None
        await session.commit()

    await message.answer("✅ Описание обновлено")


@router.callback_query(ClanMenu.filter(F.action == "leave_confirm"))
async def cb_leave_confirm(query: CallbackQuery) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "⚠️ <b>Покинуть клан?</b>\n\n"
        "Ты потеряешь доступ к бонусам.\n"
        "Если ты лидер — передай лидерство или распусти клан.",
        get_leave_confirm(),
    )


@router.callback_query(ClanMenu.filter(F.action == "leave"))
async def cb_leave(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await leave_clan(session, user)

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    disbanded = (result.data or {}).get("disbanded", False)

    if disbanded:
        await safe_render(query, "💥 <b>Клан распущен</b>", get_no_clan_menu())
    else:
        await safe_render(query, "✅ <b>Ты покинул клан</b>", get_no_clan_menu())


@router.callback_query(ClanMenu.filter(F.action == "disband_confirm"))
async def cb_disband_confirm(query: CallbackQuery) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "💥 <b>Распустить клан?</b>\n\n"
        "Все участники потеряют доступ.\n"
        "Действие необратимо.",
        get_disband_confirm(),
    )


@router.callback_query(ClanMenu.filter(F.action == "disband"))
async def cb_disband(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member.role != "leader":
            await safe_answer(query, "⛔ Только лидер", show_alert=True)
            return

        clan.is_active = False

        from sqlalchemy import delete
        from db.models import ClanLog
        await session.execute(
            delete(ClanMember).where(ClanMember.clan_id == clan.id)
        )

        session.add(ClanLog(
            clan_id=clan.id,
            user_id=user.id,
            action="disband",
            note="Лидер распустил клан",
        ))
        await session.commit()

    await safe_render(query, "💥 <b>Клан распущен</b>", get_no_clan_menu())


# ═════════════════════════════════════════════
# ТОП
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "top"))
async def cb_top(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        top = await get_top_clans(session, limit=settings.CLAN_TOP_LIMIT)

    if not top:
        await safe_render(query, "🏆 <b>Кланов пока нет</b>", get_no_clan_menu())
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    text = "🏆 <b>Топ кланов</b>\n\n"
    for i, (clan, rating) in enumerate(top):
        medal = medals[i] if i < len(medals) else f"{i + 1}."
        text += (
            f"{medal} <b>[{clan.tag}] {clan.name}</b>\n"
            f"    ур.{clan.level} · 💰 {clan.treasury:,} · 🏆 {rating:,}\n"
        )

    await safe_render(query, text, get_top_nav())


# ═════════════════════════════════════════════
# ПРИГЛАШЕНИЯ
# ═════════════════════════════════════════════

@router.callback_query(ClanMenu.filter(F.action == "invites"))
async def cb_invites(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        invites = await get_pending_invites(session, user.id)

    if not invites:
        await safe_render(
            query,
            "📨 <b>У тебя нет приглашений</b>",
            get_no_clan_menu(),
        )
        return

    await safe_render(
        query,
        f"📨 <b>Приглашения ({len(invites)})</b>",
        get_invites_menu(invites),
    )


@router.callback_query(ClanMenu.filter(F.action == "invite_view"))
async def cb_invite_view(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        invite = await session.get(ClanInvite, callback_data.invite_id)
        if invite is None or invite.status != "pending":
            await safe_render(query, "❌ Приглашение неактуально", get_no_clan_menu())
            return

        clan = await session.get(Clan, invite.clan_id)
        from_user = await session.get(User, invite.from_user_id)

        if clan is None or from_user is None:
            await safe_render(query, "❌ Данные потеряны", get_no_clan_menu())
            return

    text = (
        f"📨 <b>Приглашение в клан</b>\n\n"
        f"🏰 <b>[{clan.tag}] {clan.name}</b>\n"
        f"👑 Уровень: <b>{clan.level}</b>\n"
        f"👤 От: @{from_user.username}\n\n"
        f"До: {invite.expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Принять?"
    )

    await safe_render(query, text, get_invite_actions(invite.id))


@router.callback_query(ClanMenu.filter(F.action == "invite_accept"))
async def cb_invite_accept(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        result = await accept_invite(session, user, callback_data.invite_id)

    if not result.ok:
        await safe_answer(query, f"❌ {result.reason}", show_alert=True)
        return

    await cb_clans(query)


@router.callback_query(ClanMenu.filter(F.action == "invite_decline"))
async def cb_invite_decline(query: CallbackQuery, callback_data: ClanMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        await decline_invite(session, user, callback_data.invite_id)

    await cb_invites(query)


@router.callback_query(ClanMenu.filter(F.action == "invite"))
async def cb_invite(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None or member is None:
            return
        if member.role not in ("leader", "officer"):
            await safe_answer(query, "⛔ Только лидер/офицер", show_alert=True)
            return

    await state.set_state(ClanState.waiting_invite_username)
    await safe_render(
        query,
        "📨 <b>Пригласить игрока</b>\n\n"
        "Введи юзернейм (без @):",
        get_invite_cancel(),
    )


@router.message(ClanState.waiting_invite_username, F.text)
async def handle_invite_username(message: Message, state: FSMContext) -> None:
    username = message.text.strip().lstrip("@").lower()
    await state.clear()

    if len(username) < 3:
        await message.answer("❌ Минимум 3 символа")
        return

    async with AsyncSessionLocal() as session:
        me = await _get_db_user(session, message.from_user.id)
        if me is None:
            return

        target = (await session.execute(
            select(User).where(User.username_normalized == username)
        )).scalar_one_or_none()

        if target is None:
            await message.answer(f"❌ @{username} не найден")
            return

        result = await create_invite(session, me, target.id)

    if not result.ok:
        await message.answer(f"❌ {result.reason}")
        return

    try:
        await message.bot.send_message(
            target.telegram_id,
            f"📨 <b>@{me.username} приглашает тебя в клан!</b>\n\n"
            f"Открой 🏰 Кланы → 📨 Мои приглашения",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await message.answer(f"✅ Приглашение отправлено @{target.username}")


@router.callback_query(ClanMenu.filter(F.action == "outgoing"))
async def cb_outgoing(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = await _get_db_user(session, query.from_user.id)
        if user is None:
            return
        clan, member = await get_user_clan(session, user.id)
        if clan is None:
            return
        invites = await get_clan_pending_invites(session, clan.id)

    if not invites:
        await safe_render(query, "📤 <b>Нет исходящих приглашений</b>", get_clan_menu(member.role))
        return

    await safe_render(
        query,
        f"📤 <b>Исходящие ({len(invites)})</b>",
        get_outgoing_menu(invites),
    )


# ═════════════════════════════════════════════
# NOOP
# ═════════════════════════════════════════════

@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query) 
