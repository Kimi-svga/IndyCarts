"""Аукцион: лоты, ставки, выкуп, закрытие (1.3.2). Полностью рабочий."""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.auction import (
    AuctionMenu, get_auction_main_menu, get_duration_menu,
    get_lot_actions, get_seller_lot_actions,
)
from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import (
    AUCTION_COMMISSION, AUCTION_COMMISSION_PLUS, AUCTION_DURATIONS,
    AUCTION_MIN_BID_STEP, RARITY_EMOJI, RARITY_NAMES,
)
from core.logger import setup_logger
from db.models import Auction, AuctionBid, Card, User, UserCard
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


class AuctionState(StatesGroup):
    waiting_price = State()
    waiting_buyout = State()
    waiting_bid = State()


# ═════════════════════════════════════════════
# ГЛАВНОЕ МЕНЮ
# ═════════════════════════════════════════════

@router.callback_query(MainMenu.filter(F.action == "auction"))
async def cb_auction(query: CallbackQuery) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        f"🎯 <b>Аукцион</b>\n\n"
        f"Комиссия: <b>{AUCTION_COMMISSION:.0f}%</b> "
        f"(<b>{AUCTION_COMMISSION_PLUS:.0f}%</b> для Indy+)\n"
        f"Шаг ставки: <b>{int(AUCTION_MIN_BID_STEP * 100)}%</b>\n\n"
        f"Выбирай:",
        get_auction_main_menu(),
    )


@router.callback_query(AuctionMenu.filter(F.action == "menu"))
async def cb_auction_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    await cb_auction(query)


# ═════════════════════════════════════════════
# ПРОСМОТР ЛОТОВ
# ═════════════════════════════════════════════

@router.callback_query(AuctionMenu.filter(F.action == "browse"))
async def cb_browse(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        lots = (await session.execute(
            select(Auction)
            .where(Auction.status == "active", Auction.ends_at > datetime.utcnow())
            .order_by(Auction.ends_at.asc())
            .limit(20)
        )).scalars().all()

    if not lots:
        await safe_render(query, "🎯 <b>Нет активных лотов</b>", get_auction_main_menu())
        return

    await _show_lot(query, lots, 0)


@router.callback_query(AuctionMenu.filter(F.action == "nav"))
async def cb_nav(query: CallbackQuery, callback_data: AuctionMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        lots = (await session.execute(
            select(Auction)
            .where(Auction.status == "active", Auction.ends_at > datetime.utcnow())
            .order_by(Auction.ends_at.asc())
            .limit(20)
        )).scalars().all()

    await _show_lot(query, lots, callback_data.index)


async def _show_lot(query: CallbackQuery, lots: list, index: int) -> None:
    index = max(0, min(index, len(lots) - 1))
    lot = lots[index]

    async with AsyncSessionLocal() as session:
        uc = await session.get(UserCard, lot.user_card_id)
        card = await session.get(Card, uc.card_id) if uc else None
        seller = await session.get(User, lot.seller_id)
        bidder = await session.get(User, lot.current_bidder_id) if lot.current_bidder_id else None

    if card is None or seller is None:
        await safe_answer(query, "❌ Лот битый", show_alert=True)
        return

    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    time_left = lot.ends_at - datetime.utcnow()
    hours = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)

    bidder_text = f"@{bidder.username}" if bidder else "—"

    text = (
        f"🎯 <b>Лот #{lot.id}</b>\n\n"
        f"{emoji} <b>{card.name}</b>\n"
        f"Продавец: @{seller.username}\n"
        f"Старт: <b>{lot.start_price:,}</b>\n"
        f"Текущая: <b>{lot.current_bid:,}</b>\n"
        f"Лидер: {bidder_text}\n"
        f"Ставок: <b>{lot.bid_count}</b>\n"
        f"До конца: <b>{hours}ч {minutes}м</b>\n\n"
        f"<b>{index + 1} / {len(lots)}</b>"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=AuctionMenu(action="nav", index=index - 1).pack())
    b.button(text=f"{index + 1}/{len(lots)}", callback_data="noop")
    if index < len(lots) - 1:
        b.button(text="➡️", callback_data=AuctionMenu(action="nav", index=index + 1).pack())
    b.button(text="💰 Ставка", callback_data=AuctionMenu(action="bid", auction_id=lot.id).pack())
    if lot.buyout_price:
        b.button(text="⚡ Выкупить", callback_data=AuctionMenu(action="buyout", auction_id=lot.id).pack())
    b.button(text="🔙 К аукциону", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(3, 2, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


# ═════════════════════════════════════════════
# СТАВКА
# ═════════════════════════════════════════════

@router.callback_query(AuctionMenu.filter(F.action == "bid"))
async def cb_bid(query: CallbackQuery, callback_data: AuctionMenu, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, callback_data.auction_id)
        if lot is None or lot.status != "active":
            await safe_answer(query, "❌ Лот неактивен", show_alert=True)
            return

        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if me is None or me.id == lot.seller_id:
            await safe_answer(query, "❌ Нельзя ставить на свой лот", show_alert=True)
            return

        min_bid = int(lot.current_bid * (1 + AUCTION_MIN_BID_STEP)) if lot.current_bid else lot.start_price

    await state.update_data(bid_lot_id=lot.id)
    await state.set_state(AuctionState.waiting_bid)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(
        query,
        f"💰 <b>Ставка на лот #{lot.id}</b>\n\n"
        f"Текущая: <b>{lot.current_bid:,}</b>\n"
        f"Минимум: <b>{min_bid:,}</b>\n\n"
        f"Введи сумму:",
        b.as_markup(),
    )


@router.message(AuctionState.waiting_bid)
async def handle_bid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lot_id = data.get("bid_lot_id")
    await state.clear()

    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Число")
        return

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, lot_id)
        if lot is None or lot.status != "active":
            await message.answer("❌ Лот неактивен")
            return

        me = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        if me is None or me.id == lot.seller_id:
            await message.answer("❌ Нельзя")
            return

        min_bid = int(lot.current_bid * (1 + AUCTION_MIN_BID_STEP)) if lot.current_bid else lot.start_price

        if amount < min_bid:
            await message.answer(f"❌ Минимум: {min_bid:,}")
            return

        if me.balance < amount:
            await message.answer(f"❌ Нужно {amount:,} монет")
            return

        if lot.current_bidder_id:
            prev = await session.get(User, lot.current_bidder_id)
            if prev:
                prev.balance += lot.current_bid
                try:
                    await message.bot.send_message(
                        prev.telegram_id,
                        f"↩️ <b>Твою ставку на лот #{lot.id} перебили</b>\n\n"
                        f"Возврат: <b>+{lot.current_bid:,}</b>",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

        me.balance -= amount
        lot.current_bid = amount
        lot.current_bidder_id = me.id
        lot.bid_count += 1

        session.add(AuctionBid(
            auction_id=lot.id,
            bidder_id=me.id,
            amount=amount,
        ))
        await session.commit()

        seller = await session.get(User, lot.seller_id)
        my_username = me.username

    await message.answer(
        f"✅ <b>Ставка принята!</b>\n\n"
        f"Лот #{lot_id}: <b>{amount:,}</b>",
        parse_mode="HTML",
    )

    if seller:
        try:
            await message.bot.send_message(
                seller.telegram_id,
                f"💰 <b>Новая ставка на лот #{lot_id}</b>\n\n"
                f"@{my_username}: <b>{amount:,}</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass


# ═════════════════════════════════════════════
# ВЫКУП
# ═════════════════════════════════════════════

@router.callback_query(AuctionMenu.filter(F.action == "buyout"))
async def cb_buyout(query: CallbackQuery, callback_data: AuctionMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, callback_data.auction_id)
        if lot is None or lot.status != "active" or not lot.buyout_price:
            await safe_answer(query, "❌ Выкуп недоступен", show_alert=True)
            return

        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if me is None or me.id == lot.seller_id:
            await safe_answer(query, "❌ Нельзя", show_alert=True)
            return

        if me.balance < lot.buyout_price:
            await safe_answer(query, f"❌ Нужно {lot.buyout_price:,}", show_alert=True)
            return

        if lot.current_bidder_id:
            prev = await session.get(User, lot.current_bidder_id)
            if prev:
                prev.balance += lot.current_bid

        seller = await session.get(User, lot.seller_id)
        commission = AUCTION_COMMISSION_PLUS if seller.plus_tier == "indy_plus" else AUCTION_COMMISSION
        fee = int(lot.buyout_price * commission / 100)
        seller.balance += lot.buyout_price - fee

        me.balance -= lot.buyout_price

        uc = await session.get(UserCard, lot.user_card_id)
        if uc:
            uc.user_id = me.id
            uc.is_locked = False

        lot.status = "sold"
        lot.sold_at = datetime.utcnow()
        await session.commit()

        seller_tg = seller.telegram_id
        me_username = me.username
        price = lot.buyout_price

    await safe_render(
        query,
        f"⚡ <b>Выкуплено!</b>\n\n"
        f"Лот #{callback_data.auction_id} за <b>{price:,}</b>",
        get_auction_main_menu(),
    )

    try:
        await query.bot.send_message(
            seller_tg,
            f"💰 <b>Лот выкуплен!</b>\n\n"
            f"@{me_username} выкупил за <b>{price:,}</b>\n"
            f"Комиссия: <b>{fee:,}</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ═════════════════════════════════════════════
# ВЫСТАВЛЕНИЕ
# ═════════════════════════════════════════════

@router.callback_query(AuctionMenu.filter(F.action == "sell_pick"))
async def cb_sell_pick(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        rows = (await session.execute(
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(
                UserCard.user_id == me.id,
                UserCard.is_locked == False,
            )
            .order_by(Card.current_price.desc())
            .limit(30)
        )).all()

    if not rows:
        await safe_render(query, "❌ Нет карт для продажи", get_auction_main_menu())
        return

    b = InlineKeyboardBuilder()
    for uc, card in rows:
        emoji = RARITY_EMOJI.get(card.rarity, "⚪")
        b.button(
            text=f"{emoji} {card.name[:30]} · {card.current_price:,}",
            callback_data=AuctionMenu(action="sell_pick_card", auction_id=uc.id).pack(),
        )
    b.button(text="🔙 Назад", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, "➕ <b>Выбери карту для продажи</b>", b.as_markup())


@router.callback_query(AuctionMenu.filter(F.action == "sell_pick_card"))
async def cb_sell_pick_card(query: CallbackQuery, callback_data: AuctionMenu, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(sell_uc_id=callback_data.auction_id)
    await state.set_state(AuctionState.waiting_price)

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Отмена", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(
        query,
        f"💰 <b>Стартовая цена</b>\n\n"
        f"Введи цену (минимум {settings.AUCTION_MIN_PRICE:,}):",
        b.as_markup(),
    )


@router.message(AuctionState.waiting_price)
async def handle_price(message: Message, state: FSMContext) -> None:
    try:
        price = int(message.text.strip())
        if price < settings.AUCTION_MIN_PRICE or price > settings.AUCTION_MAX_PRICE:
            raise ValueError
    except ValueError:
        await message.answer(f"❌ {settings.AUCTION_MIN_PRICE:,}–{settings.AUCTION_MAX_PRICE:,}")
        return

    await state.update_data(sell_price=price)
    await state.set_state(AuctionState.waiting_buyout)

    b = InlineKeyboardBuilder()
    b.button(text="Без выкупа", callback_data=AuctionMenu(action="no_buyout").pack())
    b.adjust(1)

    await message.answer(
        f"⚡ <b>Цена выкупа</b>\n\n"
        f"Введи цену выкупа (должна быть > {price:,}) или нажми «Без выкупа».",
        reply_markup=b.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(AuctionMenu.filter(F.action == "no_buyout"))
async def cb_no_buyout(query: CallbackQuery, state: FSMContext) -> None:
    await safe_answer(query)
    await state.update_data(sell_buyout=None)
    await state.set_state(None)

    b = InlineKeyboardBuilder()
    for code, (label, hours) in AUCTION_DURATIONS.items():
        b.button(text=label, callback_data=AuctionMenu(action="create", duration=code).pack())
    b.button(text="🔙 Отмена", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(2, 2, 1)

    await safe_render(query, "⏱ <b>Срок аукциона</b>", b.as_markup())


@router.message(AuctionState.waiting_buyout)
async def handle_buyout(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    price = data.get("sell_price", 0)
    try:
        buyout = int(message.text.strip())
        if buyout <= price:
            raise ValueError
    except ValueError:
        await message.answer(f"❌ Выкуп должен быть > {price:,} или нажми «Без выкупа»")
        return

    await state.update_data(sell_buyout=buyout)
    await state.set_state(None)

    b = InlineKeyboardBuilder()
    for code, (label, hours) in AUCTION_DURATIONS.items():
        b.button(text=label, callback_data=AuctionMenu(action="create", duration=code).pack())
    b.button(text="🔙 Отмена", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(2, 2, 1)

    await message.answer("⏱ <b>Срок аукциона</b>", reply_markup=b.as_markup(), parse_mode="HTML")


@router.callback_query(AuctionMenu.filter(F.action == "create"))
async def cb_create(query: CallbackQuery, callback_data: AuctionMenu, state: FSMContext) -> None:
    await safe_answer(query)

    data = await state.get_data()
    uc_id = data.get("sell_uc_id")
    price = data.get("sell_price")
    buyout = data.get("sell_buyout")
    duration_code = callback_data.duration

    if not uc_id or not price:
        await safe_render(query, "❌ Ошибка данных", get_auction_main_menu())
        return

    if duration_code not in AUCTION_DURATIONS:
        await safe_render(query, "❌ Неверный срок", get_auction_main_menu())
        return

    _, hours = AUCTION_DURATIONS[duration_code]

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        uc = await session.get(UserCard, uc_id)
        if uc is None or uc.user_id != me.id or uc.is_locked:
            await safe_render(query, "❌ Карта недоступна", get_auction_main_menu())
            return

        uc.is_locked = True

        lot = Auction(
            seller_id=me.id,
            user_card_id=uc.id,
            start_price=price,
            buyout_price=buyout,
            current_bid=0,
            bid_count=0,
            commission_percent=AUCTION_COMMISSION,
            status="active",
            ends_at=datetime.utcnow() + timedelta(hours=hours),
        )
        session.add(lot)
        await session.commit()
        await session.refresh(lot)
        lot_id = lot.id

    await state.clear()

    if buyout:
        text = (
            f"✅ <b>Лот #{lot_id} создан</b>\n\n"
            f"Старт: <b>{price:,}</b>\n"
            f"Выкуп: <b>{buyout:,}</b>"
        )
    else:
        text = (
            f"✅ <b>Лот #{lot_id} создан</b>\n\n"
            f"Старт: <b>{price:,}</b>\n"
            f"Без выкупа"
        )

    await safe_render(query, text, get_auction_main_menu())


# ═════════════════════════════════════════════
# МОИ ЛОТЫ
# ═════════════════════════════════════════════

@router.callback_query(AuctionMenu.filter(F.action == "my"))
async def cb_my(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        me = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()
        if me is None:
            return

        lots = (await session.execute(
            select(Auction)
            .where(Auction.seller_id == me.id)
            .order_by(Auction.created_at.desc())
            .limit(20)
        )).scalars().all()

    if not lots:
        await safe_render(query, "📋 <b>У тебя нет лотов</b>", get_auction_main_menu())
        return

    text = "📋 <b>Мои лоты</b>\n\n"
    for lot in lots:
        text += (
            f"#{lot.id} · {lot.status} · старт {lot.start_price:,} · "
            f"бид {lot.current_bid:,} ({lot.bid_count})\n"
        )

    b = InlineKeyboardBuilder()
    for lot in lots:
        if lot.status == "active" and lot.bid_count == 0:
            b.button(
                text=f"🚫 Отменить лот #{lot.id}",
                callback_data=AuctionMenu(action="cancel", auction_id=lot.id).pack(),
            )
    b.button(text="🔙 Назад", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(AuctionMenu.filter(F.action == "cancel"))
async def cb_cancel_lot(query: CallbackQuery, callback_data: AuctionMenu) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, callback_data.auction_id)
        if lot is None or lot.status != "active":
            await safe_answer(query, "❌ Нельзя отменить", show_alert=True)
            return

        if lot.bid_count > 0:
            await safe_answer(query, "❌ Уже есть ставки", show_alert=True)
            return

        lot.status = "cancelled"

        uc = await session.get(UserCard, lot.user_card_id)
        if uc:
            uc.is_locked = False

        await session.commit()

    await safe_render(query, "🚫 <b>Лот отменён</b>", get_auction_main_menu())


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query) 
