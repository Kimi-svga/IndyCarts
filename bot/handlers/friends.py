"""Друзья: список, заявки, поиск, карточка."""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import and_, delete, func, or_, select

from bot.keyboards.friends import (
    FriendsMenu, get_back_to_friends, get_friend_actions,
    get_friends_menu, get_request_actions, get_user_actions,
)
from bot.keyboards.main import get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.logger import setup_logger
from db.models import Friend, FriendRequest, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()

ONLINE_THRESHOLD_MIN = 15


class FriendsState(StatesGroup):
    waiting_nickname = State()


def _online_status(last_seen: datetime | None) -> str:
    if last_seen is None:
        return "⚪ давно"
    diff = datetime.utcnow() - last_seen
    if diff < timedelta(minutes=ONLINE_THRESHOLD_MIN):
        return "🟢 онлайн"
    if diff < timedelta(hours=1):
        return f"⚪ {diff.seconds // 60}м"
    if diff < timedelta(days=1):
        return f"⚪ {diff.seconds // 3600}ч"
    return f"⚪ {diff.days}д"


async def _get_counts(session, user_id: int) -> tuple[int, int, int]:
    friends = (await session.execute(
        select(func.count(Friend.id)).where(Friend.user_id == user_id)
    )).scalar() or 0

    incoming = (await session.execute(
        select(func.count(FriendRequest.id)).where(
            FriendRequest.to_user_id == user_id,
            FriendRequest.status == "pending",
        )
    )).scalar() or 0

    outgoing = (await session.execute(
        select(func.count(FriendRequest.id)).where(
            FriendRequest.from_user_id == user_id,
            FriendRequest.status == "pending",
        )
    )).scalar() or 0

    return friends, incoming, outgoing


@router.callback_query(FriendsMenu.filter(F.action == "menu"))
async def cb_menu(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        friends, incoming, outgoing = await _get_counts(session, user.id)

    text = (
        f"👥 <b>Друзья</b>\n\n"
        f"👤 Всего: <b>{friends}</b>\n"
        f"📥 Заявки: <b>{incoming}</b>\n"
        f"📤 Исходящие: <b>{outgoing}</b>"
    )
    await safe_render(query, text, get_friends_menu(friends, incoming, outgoing))


@router.callback_query(FriendsMenu.filter(F.action == "list"))
async def cb_list(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if me is None:
            return

        rows = (await session.execute(
            select(Friend, User)
            .join(User, Friend.friend_id == User.id)
            .where(Friend.user_id == me.id)
            .order_by(User.last_seen_at.desc())
            .limit(30)
        )).all()

        friends, incoming, outgoing = await _get_counts(session, me.id)

    if not rows:
        await safe_render(
            query,
            "👥 <b>Пока нет друзей</b>\n\nНайди игрока по нику и добавь.",
            get_friends_menu(0, incoming, outgoing),
        )
        return

    text = f"👥 <b>Мои друзья</b> ({len(rows)})\n\n"
    b = InlineKeyboardBuilder()
    for friend, u in rows:
        status = _online_status(u.last_seen_at)
        b.button(
            text=f"{status} @{u.username}",
            callback_data=FriendsMenu(action="view", user_id=u.id).pack(),
        )
    b.button(text="🔙 Назад", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(FriendsMenu.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        friend = await session.get(User, callback_data.user_id)
        if friend is None:
            await safe_answer(query, "❌ Игрок не найден", show_alert=True)
            return

    status = _online_status(friend.last_seen_at)

    text = (
        f"👤 <b>@{friend.username}</b> {status}\n\n"
        f"⚔️ PvP: <b>{friend.pvp_rating}</b> "
        f"({friend.pvp_wins_total}W/{friend.pvp_losses_total}L)\n"
        f"🔥 Стрик: <b>{friend.daily_streak}</b>\n"
        f"💎 Indy+: {'да' if friend.plus_tier == 'indy_plus' else 'нет'}\n"
        f"📅 Регистрация: {friend.created_at.strftime('%d.%m.%Y')}"
    )

    await safe_render(query, text, get_friend_actions(friend.id))


@router.callback_query(FriendsMenu.filter(F.action == "incoming"))
async def cb_incoming(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        rows = (await session.execute(
            select(FriendRequest, User)
            .join(User, FriendRequest.from_user_id == User.id)
            .where(
                FriendRequest.to_user_id == me.id,
                FriendRequest.status == "pending",
            )
            .order_by(FriendRequest.created_at.desc())
            .limit(20)
        )).all()

    if not rows:
        await safe_render(query, "📥 <b>Нет входящих заявок</b>", get_back_to_friends())
        return

    text = "📥 <b>Входящие заявки</b>\n\n"
    b = InlineKeyboardBuilder()
    for req, u in rows:
        b.button(
            text=f"📨 @{u.username}",
            callback_data=FriendsMenu(action="req_view", request_id=req.id).pack(),
        )
    b.button(text="🔙 К друзьям", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(FriendsMenu.filter(F.action == "req_view"))
async def cb_req_view(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        req = await session.get(FriendRequest, callback_data.request_id)
        if req is None or req.status != "pending":
            await safe_answer(query, "❌ Заявка неактуальна", show_alert=True)
            return
        from_user = await session.get(User, req.from_user_id)
        if from_user is None:
            return

    status = _online_status(from_user.last_seen_at)
    text = (
        f"📨 <b>Заявка от @{from_user.username}</b> {status}\n\n"
        f"⚔️ PvP: {from_user.pvp_rating}\n"
        f"🔥 Стрик: {from_user.daily_streak}\n"
        f"📅 Регистрация: {from_user.created_at.strftime('%d.%m.%Y')}\n\n"
        f"Принять?"
    )
    await safe_render(query, text, get_request_actions(req.id))


@router.callback_query(FriendsMenu.filter(F.action == "accept"))
async def cb_accept(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        req = await session.get(FriendRequest, callback_data.request_id)
        if req is None or req.status != "pending" or me is None:
            await safe_answer(query, "❌ Уже обработано", show_alert=True)
            return

        if req.to_user_id != me.id:
            return

        session.add(Friend(user_id=me.id, friend_id=req.from_user_id))
        session.add(Friend(user_id=req.from_user_id, friend_id=me.id))

        req.status = "accepted"
        req.resolved_at = datetime.utcnow()

        from_user = await session.get(User, req.from_user_id)
        await session.commit()

        if from_user:
            try:
                await query.bot.send_message(
                    from_user.telegram_id,
                    f"✅ <b>@{me.username} принял заявку в друзья!</b>",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    await safe_render(query, "✅ <b>Заявка принята</b>", get_back_to_friends())


@router.callback_query(FriendsMenu.filter(F.action == "reject"))
async def cb_reject(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        req = await session.get(FriendRequest, callback_data.request_id)
        if req is None or req.status != "pending" or me is None:
            return
        if req.to_user_id != me.id:
            return

        req.status = "rejected"
        req.resolved_at = datetime.utcnow()
        await session.commit()

    await safe_render(query, "❌ <b>Заявка отклонена</b>", get_back_to_friends())


@router.callback_query(FriendsMenu.filter(F.action == "outgoing"))
async def cb_outgoing(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        rows = (await session.execute(
            select(FriendRequest, User)
            .join(User, FriendRequest.to_user_id == User.id)
            .where(
                FriendRequest.from_user_id == me.id,
                FriendRequest.status == "pending",
            )
            .limit(20)
        )).all()

    if not rows:
        await safe_render(query, "📤 <b>Нет исходящих</b>", get_back_to_friends())
        return

    text = "📤 <b>Исходящие заявки</b>\n\n"
    for req, u in rows:
        text += f"⏳ @{u.username}\n"

    await safe_render(query, text, get_back_to_friends())


@router.callback_query(FriendsMenu.filter(F.action == "search"))
async def cb_search(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(FriendsState.waiting_nickname)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, "🔍 <b>Поиск игрока</b>\n\nВведи ник (без @):", b.as_markup())


@router.message(FriendsState.waiting_nickname)
async def handle_nickname(message: Message, state: FSMContext) -> None:
    nick = message.text.strip().lstrip("@").lower()
    await state.clear()

    if len(nick) < 3:
        await message.answer("❌ Минимум 3 символа")
        return

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        target = (await session.execute(
            select(User).where(User.username_normalized == nick)
        )).scalar_one_or_none()

        if me is None:
            return

        if target is None:
            await message.answer(f"❌ @{nick} не найден", reply_markup=get_back_to_friends())
            return

        if target.id == me.id:
            await message.answer("❌ Нельзя добавить себя", reply_markup=get_back_to_friends())
            return

        is_friend = (await session.execute(
            select(Friend).where(Friend.user_id == me.id, Friend.friend_id == target.id)
        )).scalar_one_or_none() is not None

        pending = (await session.execute(
            select(FriendRequest).where(
                FriendRequest.from_user_id == me.id,
                FriendRequest.to_user_id == target.id,
                FriendRequest.status == "pending",
            )
        )).scalar_one_or_none() is not None

    status = _online_status(target.last_seen_at)
    text = (
        f"👤 <b>@{target.username}</b> {status}\n\n"
        f"⚔️ PvP: <b>{target.pvp_rating}</b>\n"
        f"🔥 Стрик: <b>{target.daily_streak}</b>\n"
        f"📅 Регистрация: {target.created_at.strftime('%d.%m.%Y')}"
    )

    await message.answer(text, reply_markup=get_user_actions(target.id, is_friend, pending), parse_mode="HTML")


@router.callback_query(FriendsMenu.filter(F.action == "add"))
async def cb_add(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        target = await session.get(User, callback_data.user_id)
        if me is None or target is None or me.id == target.id:
            return

        exists = (await session.execute(
            select(Friend).where(Friend.user_id == me.id, Friend.friend_id == target.id)
        )).scalar_one_or_none()
        if exists:
            await safe_answer(query, "✅ Уже в друзьях", show_alert=True)
            return

        req_exists = (await session.execute(
            select(FriendRequest).where(
                FriendRequest.from_user_id == me.id,
                FriendRequest.to_user_id == target.id,
                FriendRequest.status == "pending",
            )
        )).scalar_one_or_none()
        if req_exists:
            await safe_answer(query, "⏳ Заявка уже отправлена", show_alert=True)
            return

        session.add(FriendRequest(from_user_id=me.id, to_user_id=target.id, status="pending"))
        await session.commit()

        target_tg = target.telegram_id
        me_username = me.username

    try:
        await query.bot.send_message(
            target_tg,
            f"📨 <b>@{me_username} хочет добавить тебя в друзья!</b>\n\n"
            f"Открой профиль → 👥 Друзья",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await safe_render(query, "✅ <b>Заявка отправлена</b>", get_back_to_friends())


@router.callback_query(FriendsMenu.filter(F.action == "remove"))
async def cb_remove(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        await session.execute(
            delete(Friend).where(
                or_(
                    and_(Friend.user_id == me.id, Friend.friend_id == callback_data.user_id),
                    and_(Friend.user_id == callback_data.user_id, Friend.friend_id == me.id),
                )
            )
        )
        await session.commit()

    await safe_render(query, "❌ <b>Удалено из друзей</b>", get_back_to_friends())


@router.callback_query(FriendsMenu.filter(F.action == "duel"))
async def cb_duel(query: CallbackQuery, callback_data: FriendsMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        target = await session.get(User, callback_data.user_id)
        if target is None:
            return
        nick = target.username

    await safe_render(
        query,
        f"⚔️ <b>Вызов на PvP</b>\n\n"
        f"Отправь команду:\n<code>/duel @{nick}</code>",
        get_back_to_friends(),
    )


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query)
