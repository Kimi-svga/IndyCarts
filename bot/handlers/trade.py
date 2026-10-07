"""Обмен картами между игроками (1.3.1). Полностью рабочий."""

import json
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.friends import FriendsMenu, get_back_to_friends
from bot.keyboards.main import get_back_menu
from bot.keyboards.trade import TradeMenu, get_trade_offer_actions
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    RARITY_EMOJI, TRADE_MAX_CARDS, TRADE_MAX_MONEY, TRADE_TIMEOUT_HOURS,
)
from core.logger import setup_logger
from db.models import Card, Trade, User, UserCard
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


class TradeState(StatesGroup):
    picking = State()
    waiting_money = State()


def _parse_cards(s: str) -> list[int]:
    try:
        return [int(x) for x in json.loads(s or "[]")]
    except Exception:
        return []


def _dump_cards(ids: list[int]) -> str:
    return json.dumps(ids)


async def _render_trade_screen(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    target_id = data.get("target_id")
    offer = data.get("offer_cards", [])
    request = data.get("request_cards", [])
    offer_money = data.get("offer_money", 0)

    async with AsyncSessionLocal() as session:
        target = await session.get(User, target_id)
        target_username = target.username if target else "?"

    text = (
        f"🃏 <b>Обмен с @{target_username}</b>\n\n"
        f"📤 Твои карты: <b>{len(offer)}</b>/{TRADE_MAX_CARDS}\n"
        f"📥 Его карты: <b>{len(request)}</b>/{TRADE_MAX_CARDS}\n"
        f"💰 Деньги: <b>{offer_money:,}</b>\n\n"
        f"Выбирай карты или отправь запрос."
    )

    b = InlineKeyboardBuilder()
    b.button(
        text=f"📤 Мои карты ({len(offer)})",
        callback_data=TradeMenu(action="pick_offer", user_id=target_id).pack(),
    )
    b.button(
        text=f"📥 Его карты ({len(request)})",
        callback_data=TradeMenu(action="pick_request", user_id=target_id).pack(),
    )
    b.button(
        text=f"💰 Деньги ({offer_money:,})",
        callback_data=TradeMenu(action="money", user_id=target_id).pack(),
    )
    b.button(
        text="✅ Отправить",
        callback_data=TradeMenu(action="send", user_id=target_id).pack(),
    )
    b.button(
        text="🔙 Отмена",
        callback_data=TradeMenu(action="cancel_draft", user_id=target_id).pack(),
    )
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(FriendsMenu.filter(F.action == "trade"))
async def cb_trade_start(query: CallbackQuery, callback_data: FriendsMenu, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        target = await session.get(User, callback_data.user_id)
        if target is None:
            await safe_answer(query, "❌ Игрок не найден", show_alert=True)
            return

    await state.clear()
    await state.update_data(
        target_id=callback_data.user_id,
        offer_cards=[],
        request_cards=[],
        offer_money=0,
    )
    await state.set_state(TradeState.picking)

    await _render_trade_screen(query, state)


@router.callback_query(TradeMenu.filter(F.action == "back_to_start"))
async def cb_back_to_start(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await _render_trade_screen(query, state)


@router.callback_query(TradeMenu.filter(F.action == "cancel_draft"))
async def cb_cancel_draft(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.clear()
    await safe_render(query, "🚫 <b>Обмен отменён</b>", get_back_to_friends())


@router.callback_query(TradeMenu.filter(F.action == "pick_offer"))
async def cb_pick_offer(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await _show_picker(query, state, 0, "offer")


@router.callback_query(TradeMenu.filter(F.action == "pick_request"))
async def cb_pick_request(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await _show_picker(query, state, 0, "request")


@router.callback_query(TradeMenu.filter(F.action == "nav_offer"))
async def cb_nav_offer(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await _show_picker(query, state, callback_data.index, "offer")


@router.callback_query(TradeMenu.filter(F.action == "nav_request"))
async def cb_nav_request(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await _show_picker(query, state, callback_data.index, "request")


async def _show_picker(query: CallbackQuery, state: FSMContext, index: int, side: str) -> None:
    data = await state.get_data()
    target_id = data.get("target_id")
    chosen = set(data.get(f"{side}_cards", []))

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        owner_id = me.id if side == "offer" else target_id

        rows = (await session.execute(
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(
                UserCard.user_id == owner_id,
                UserCard.is_locked == False,
            )
            .order_by(Card.current_price.desc())
            .limit(50)
        )).all()

    if not rows:
        await _render_trade_screen(query, state)
        return

    index = max(0, min(index, len(rows) - 1))
    uc, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    is_chosen = uc.id in chosen

    title = "📤 Твои карты" if side == "offer" else "📥 Его карты"
    mark = "✅ " if is_chosen else ""

    text = (
        f"<b>{title}</b>\n\n"
        f"{mark}{emoji} <b>{card.name}</b>\n"
        f"Цена: <b>{card.current_price:,}</b>\n\n"
        f"Выбрано: <b>{len(chosen)}</b>/{TRADE_MAX_CARDS}\n"
        f"{index + 1} / {len(rows)}"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=TradeMenu(action=f"nav_{side}", user_id=target_id, index=index - 1).pack())
    b.button(text=f"{index + 1}/{len(rows)}", callback_data="noop")
    if index < len(rows) - 1:
        b.button(text="➡️", callback_data=TradeMenu(action=f"nav_{side}", user_id=target_id, index=index + 1).pack())

    if is_chosen:
        b.button(
            text="➖ Убрать",
            callback_data=TradeMenu(action=f"toggle_{side}", user_id=target_id, uc_id=uc.id, index=index).pack(),
        )
    else:
        b.button(
            text="➕ Выбрать",
            callback_data=TradeMenu(action=f"toggle_{side}", user_id=target_id, uc_id=uc.id, index=index).pack(),
        )

    b.button(
        text="🔙 К обмену",
        callback_data=TradeMenu(action="back_to_start", user_id=target_id).pack(),
    )
    b.adjust(3, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(TradeMenu.filter(F.action.startswith("toggle_")))
async def cb_toggle(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)

    side = "offer" if callback_data.action == "toggle_offer" else "request"
    uc_id = callback_data.uc_id

    data = await state.get_data()
    chosen = list(data.get(f"{side}_cards", []))

    if uc_id in chosen:
        chosen.remove(uc_id)
    else:
        if len(chosen) >= TRADE_MAX_CARDS:
            await safe_answer(query, f"❌ Максимум {TRADE_MAX_CARDS}", show_alert=True)
            return

        other = "request" if side == "offer" else "offer"
        if uc_id in data.get(f"{other}_cards", []):
            await safe_answer(query, "❌ Карта уже в другой стороне", show_alert=True)
            return

        chosen.append(uc_id)

    await state.update_data(**{f"{side}_cards": chosen})
    await _show_picker(query, state, callback_data.index, side)


@router.callback_query(TradeMenu.filter(F.action == "money"))
async def cb_money(query: CallbackQuery, callback_data: TradeMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await state.set_state(TradeState.waiting_money)

    b = InlineKeyboardBuilder()
    b.button(
        text="🔙 Отмена",
        callback_data=TradeMenu(action="back_to_start", user_id=callback_data.user_id).pack(),
    )
    b.adjust(1)

    await safe_render(
        query,
        f"💰 <b>Деньги в обмене</b>\n\n"
        f"Введи сумму, которую ты отдаёшь:\n"
        f"<code>0</code> — без денег\n"
        f"Максимум: <b>{TRADE_MAX_MONEY:,}</b>",
        b.as_markup(),
    )


@router.message(TradeState.waiting_money)
async def handle_money(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        if amount < 0 or amount > TRADE_MAX_MONEY:
            raise ValueError
    except ValueError:
        await message.answer(f"❌ Число 0–{TRADE_MAX_MONEY:,}")
        return

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return
        if me.balance < amount:
            await message.answer(f"❌ У тебя только {me.balance:,} монет")
            return

    await state.update_data(offer_money=amount)
    await state.set_state(TradeState.picking)

    await message.answer(
        f"💰 Деньги: <b>{amount:,}</b>\n\nПродолжай обмен.",
        parse_mode="HTML",
    )


@router.callback_query(TradeMenu.filter(F.action == "send"))
async def cb_send(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    target_id = data.get("target_id")
    offer = data.get("offer_cards", [])
    request = data.get("request_cards", [])
    offer_money = data.get("offer_money", 0)

    if not offer and not request and not offer_money:
        await safe_answer(query, "❌ Пустой обмен", show_alert=True)
        return

    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        target = await session.get(User, target_id)

        if me is None or target is None:
            return

        if me.balance < offer_money:
            await safe_answer(query, "❌ Не хватает монет", show_alert=True)
            return

        if offer:
            for uc_id in offer:
                uc = await session.get(UserCard, uc_id)
                if uc and uc.user_id == me.id and not uc.is_locked:
                    uc.is_locked = True
                else:
                    await safe_answer(query, "❌ Карта недоступна", show_alert=True)
                    return

        trade = Trade(
            initiator_id=me.id,
            target_id=target.id,
            offer_cards=_dump_cards(offer),
            request_cards=_dump_cards(request),
            offer_money=offer_money,
            request_money=0,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=TRADE_TIMEOUT_HOURS),
        )
        session.add(trade)
        await session.commit()
        await session.refresh(trade)
        trade_id = trade.id
        me_username = me.username
        target_tg = target.telegram_id
        target_username = target.username

    await state.clear()

    await safe_render(
        query,
        f"✅ <b>Обмен отправлен @{target_username}</b>\n\nЖдём ответа.",
        get_back_to_friends(),
    )

    summary = await _build_trade_summary(trade_id)

    try:
        await query.bot.send_message(
            target_tg,
            f"📨 <b>@{me_username} предлагает обмен</b>\n\n{summary}",
            parse_mode="HTML",
            reply_markup=get_trade_offer_actions(trade_id),
        )
    except Exception as e:
        logger.error(f"trade notify: {e}")


async def _build_trade_summary(trade_id: int) -> str:
    async with AsyncSessionLocal() as session:
        trade = await session.get(Trade, trade_id)
        if trade is None:
            return ""

        initiator = await session.get(User, trade.initiator_id)
        offer_ids = _parse_cards(trade.offer_cards)
        request_ids = _parse_cards(trade.request_cards)

        offer_names = []
        for uc_id in offer_ids:
            uc = await session.get(UserCard, uc_id)
            if uc:
                card = await session.get(Card, uc.card_id)
                if card:
                    offer_names.append(card.name)

        request_names = []
        for uc_id in request_ids:
            uc = await session.get(UserCard, uc_id)
            if uc:
                card = await session.get(Card, uc.card_id)
                if card:
                    request_names.append(card.name)

    lines = [f"👤 От: @{initiator.username if initiator else '?'}"]

    if offer_names:
        lines.append("\n📤 Отдаёт:")
        for n in offer_names:
            lines.append(f"• {n}")
    if trade.offer_money:
        lines.append(f"• 💰 {trade.offer_money:,}")

    if request_names:
        lines.append("\n📥 Просит:")
        for n in request_names:
            lines.append(f"• {n}")

    return "\n".join(lines)


@router.callback_query(TradeMenu.filter(F.action == "accept"))
async def cb_accept(query: CallbackQuery, callback_data: TradeMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        trade = await session.get(Trade, callback_data.trade_id)
        if trade is None or trade.status != "pending":
            await safe_answer(query, "❌ Сделка неактуальна", show_alert=True)
            return

        if trade.expires_at < datetime.utcnow():
            trade.status = "expired"
            await session.commit()
            await safe_answer(query, "⌛ Сделка истекла", show_alert=True)
            return

        offer_ids = _parse_cards(trade.offer_cards)
        request_ids = _parse_cards(trade.request_cards)

        cards_a = []
        for uc_id in offer_ids:
            uc = await session.get(UserCard, uc_id)
            if uc is None or uc.user_id != trade.initiator_id:
                trade.status = "cancelled"
                await session.commit()
                await safe_answer(query, "❌ У инициатора нет карт", show_alert=True)
                return
            cards_a.append(uc)

        cards_b = []
        for uc_id in request_ids:
            uc = await session.get(UserCard, uc_id)
            if uc is None or uc.user_id != trade.target_id:
                trade.status = "cancelled"
                await session.commit()
                await safe_answer(query, "❌ У тебя нет карт", show_alert=True)
                return
            cards_b.append(uc)

        initiator = await session.get(User, trade.initiator_id)
        target = await session.get(User, trade.target_id)

        if initiator.balance < trade.offer_money:
            trade.status = "cancelled"
            await session.commit()
            await safe_answer(query, "❌ У инициатора нет монет", show_alert=True)
            return

        for uc in cards_a:
            uc.user_id = trade.target_id
            uc.is_locked = False

        for uc in cards_b:
            uc.user_id = trade.initiator_id
            uc.is_locked = False

        initiator.balance -= trade.offer_money
        target.balance += trade.offer_money

        trade.status = "accepted"
        trade.resolved_at = datetime.utcnow()
        await session.commit()

        initiator_tg = initiator.telegram_id
        target_username = target.username

    await safe_render(query, "✅ <b>Обмен принят!</b>", get_back_to_friends())

    try:
        await query.bot.send_message(
            initiator_tg,
            f"✅ <b>@{target_username} принял обмен!</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.callback_query(TradeMenu.filter(F.action == "decline"))
async def cb_decline(query: CallbackQuery, callback_data: TradeMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        trade = await session.get(Trade, callback_data.trade_id)
        if trade is None or trade.status != "pending":
            return

        trade.status = "declined"
        trade.resolved_at = datetime.utcnow()

        for uc_id in _parse_cards(trade.offer_cards) + _parse_cards(trade.request_cards):
            uc = await session.get(UserCard, uc_id)
            if uc:
                uc.is_locked = False

        await session.commit()
        initiator = await session.get(User, trade.initiator_id)
        target_username = (await session.get(User, trade.target_id)).username

    await safe_render(query, "❌ <b>Обмен отклонён</b>", get_back_to_friends())

    if initiator:
        try:
            await query.bot.send_message(
                initiator.telegram_id,
                f"❌ <b>@{target_username} отклонил обмен</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass


@router.callback_query(TradeMenu.filter(F.action == "cancel"))
async def cb_cancel(query: CallbackQuery, callback_data: TradeMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        trade = await session.get(Trade, callback_data.trade_id)
        if trade is None or trade.status != "pending":
            return

        trade.status = "cancelled"
        trade.resolved_at = datetime.utcnow()

        for uc_id in _parse_cards(trade.offer_cards) + _parse_cards(trade.request_cards):
            uc = await session.get(UserCard, uc_id)
            if uc:
                uc.is_locked = False

        await session.commit()

    await safe_render(query, "🚫 <b>Обмен отменён</b>", get_back_to_friends())


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query) 
