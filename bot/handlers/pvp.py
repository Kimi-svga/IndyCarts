"""PvP-дуэли на кубах."""

import random

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import RARITY_EMOJI, RARITY_NAMES
from db.models import Card, PvpBattle, User, UserCard
from db.session import AsyncSessionLocal
from services.pvp import calculate_elo

router = Router()


class PvpAction(CallbackData, prefix="pvp"):
    """Действие в PvP."""
    action: str
    battle_id: int


class PvpBet(CallbackData, prefix="pvpbet"):
    """Ставка в PvP."""
    battle_id: int
    user_card_id: int


@router.callback_query(MainMenu.filter(F.action == "pvp"))
async def cb_pvp(query: CallbackQuery) -> None:
    """Открывает PvP-меню."""
    await safe_answer(query)
    await safe_render(
        query,
        f"⚔️ <b>PvP Кубы</b>\n\n"
        f"Вызови игрока:\n<code>/duel @username</code>\n\n"
        f"Стоимость: {settings.PVP_FEE} монет\n"
        f"Победитель забирает карту.",
        get_back_menu(),
    )


@router.message(F.text.startswith("/duel"))
async def cmd_duel(message: Message) -> None:
    """Создаёт вызов на дуэль."""
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/duel @username</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        challenger = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        opponent = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if challenger is None:
            await message.answer("❌ Сначала /start")
            return
        if opponent is None:
            await message.answer("❌ Игрок не найден")
            return
        if challenger.id == opponent.id:
            await message.answer("❌ Нельзя вызвать себя")
            return
        if challenger.balance < settings.PVP_FEE:
            await message.answer(f"❌ Нужно {settings.PVP_FEE} монет")
            return

        battle = PvpBattle(
            challenger_id=challenger.id,
            opponent_id=opponent.id,
            status="pending",
        )
        session.add(battle)
        await session.commit()
        battle_id = battle.id
        opponent_tg = opponent.telegram_id
        challenger_name = challenger.username

    b = InlineKeyboardBuilder()
    b.button(text="✅ Принять", callback_data=PvpAction(action="choose_card", battle_id=battle_id))
    b.button(text="❌ Отклонить", callback_data=PvpAction(action="decline", battle_id=battle_id))
    b.adjust(2)

    try:
        await message.bot.send_message(
            opponent_tg,
            f"⚔️ <b>Вызов на PvP!</b>\n\n"
            f"От: <b>@{challenger_name}</b>\n\n"
            f"Стоимость: {settings.PVP_FEE} монет\n"
            f"Победитель забирает карту.\n\n"
            f"Принять?",
            reply_markup=b.as_markup(),
            parse_mode="HTML",
        )
    except Exception:
        await message.answer("❌ Не удалось отправить вызов")

    await message.answer(f"⚔️ Вызов отправлен @{target}!")


@router.callback_query(PvpAction.filter(F.action == "decline"))
async def cb_pvp_decline(query: CallbackQuery, callback_data: PvpAction) -> None:
    """Отклонение вызова."""
    await safe_answer(query, "❌ Вызов отклонён")

    async with AsyncSessionLocal() as session:
        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == callback_data.battle_id)
        )).scalar_one_or_none()

        if battle is not None:
            battle.status = "declined"
            await session.commit()

            challenger = (await session.execute(
                select(User).where(User.id == battle.challenger_id)
            )).scalar_one_or_none()
            challenger_tg = challenger.telegram_id
            opponent_name = query.from_user.username

    await safe_render(query, "❌ Вызов отклонён.", get_back_menu())

    try:
        await query.bot.send_message(
            challenger_tg,
            f"❌ <b>@{opponent_name}</b> отклонил вызов.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.callback_query(PvpAction.filter(F.action == "choose_card"))
async def cb_pvp_choose_card(query: CallbackQuery, callback_data: PvpAction) -> None:
    """Начинает выбор карты для ставки."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )
        rows = (await session.execute(stmt)).all()

    if not rows:
        await safe_answer(query, "❌ У тебя нет карт", show_alert=True)
        return

    await show_card_for_bet(query, rows, 0, callback_data.battle_id)


async def show_card_for_bet(query: CallbackQuery, rows: list, index: int, battle_id: int) -> None:
    """Показывает карту для ставки в карусели."""
    user_card, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")

    text = (
        f"🎁 <b>Выбери карту для ставки</b>\n\n"
        f"{emoji} <b>{card.name}</b>\n"
        f"Редкость: {RARITY_NAMES[card.rarity]}\n"
        f"Цена: {card.current_price}\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(rows)}</b>"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=f"btn_{battle_id}_{index - 1}")
    b.button(text=f"{index + 1}/{len(rows)}", callback_data="noop")
    if index < len(rows) - 1:
        b.button(text="➡️", callback_data=f"btn_{battle_id}_{index + 1}")
    b.button(text="✅ Поставить", callback_data=PvpBet(battle_id=battle_id, user_card_id=user_card.id))
    b.button(text="🔙 Отмена", callback_data=PvpAction(action="decline", battle_id=battle_id))
    b.adjust(3, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(F.data.startswith("btn_"))
async def cb_bet_nav(query: CallbackQuery) -> None:
    """Навигация по картам для ставки."""
    await safe_answer(query)
    _, battle_id, index = query.data.split("_")
    battle_id = int(battle_id)
    index = int(index)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )
        rows = (await session.execute(stmt)).all()

    await show_card_for_bet(query, rows, index, battle_id)


@router.callback_query(PvpBet.filter())
async def cb_pvp_bet_confirm(query: CallbackQuery, callback_data: PvpBet) -> None:
    """Подтверждение ставки и бой."""
    await safe_answer(query)
    await _finish_pvp(query, callback_data.battle_id, callback_data.user_card_id)


async def _finish_pvp(query: CallbackQuery, battle_id: int, chosen_card_id: int | None) -> None:
    """Логика дуэли: кубы, Эло, передача карты."""
    async with AsyncSessionLocal() as session:
        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == battle_id)
        )).scalar_one_or_none()

        if battle is None or battle.status != "pending":
            await safe_answer(query, "❌ Вызов уже неактуален", show_alert=True)
            return

        challenger = (await session.execute(
            select(User).where(User.id == battle.challenger_id)
        )).scalar_one_or_none()

        opponent = (await session.execute(
            select(User).where(User.id == battle.opponent_id)
        )).scalar_one_or_none()

        if challenger.balance < settings.PVP_FEE or opponent.balance < settings.PVP_FEE:
            await safe_answer(query, f"❌ У кого-то нет {settings.PVP_FEE} монет", show_alert=True)
            battle.status = "cancelled"
            await session.commit()
            return

        challenger.balance -= settings.PVP_FEE
        opponent.balance -= settings.PVP_FEE

        cr = random.randint(1, 6) + random.randint(1, 6)
        orr = random.randint(1, 6) + random.randint(1, 6)
        while cr == orr:
            cr = random.randint(1, 6) + random.randint(1, 6)
            orr = random.randint(1, 6) + random.randint(1, 6)

        winner, loser = (challenger, opponent) if cr > orr else (opponent, challenger)

        # Эло
        elo = calculate_elo(winner.pvp_rating, loser.pvp_rating)
        winner.pvp_rating += elo.winner_delta
        loser.pvp_rating += elo.loser_delta

        if loser.pvp_rating < 100:
            loser.pvp_rating = 100

        card_name = "ничего"
        if chosen_card_id is not None:
            user_card = (await session.execute(
                select(UserCard).where(
                    UserCard.id == chosen_card_id,
                    UserCard.user_id == loser.id,
                )
            )).scalar_one_or_none()
        else:
            user_card = (await session.execute(
                select(UserCard).where(UserCard.user_id == loser.id).limit(1)
            )).scalar_one_or_none()

        if user_card is not None:
            card = (await session.execute(
                select(Card).where(Card.id == user_card.card_id)
            )).scalar_one_or_none()
            card_name = card.name
            user_card.user_id = winner.id

        winner.pvp_wins += 1
        loser.pvp_losses += 1

        battle.status = "finished"
        battle.challenger_roll = cr
        battle.opponent_roll = orr
        battle.winner_id = winner.id
        await session.commit()

        c_name = challenger.username
        o_name = opponent.username
        w_name = winner.username
        challenger_tg = challenger.telegram_id
        opponent_tg = opponent.telegram_id

    text = (
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"🎲 @{c_name}: {cr}\n"
        f"🎲 @{o_name}: {orr}\n\n"
        f"🏆 Победитель: <b>@{w_name}</b>\n"
        f"Забирает: {card_name}\n\n"
        f"📈 Рейтинг: <b>{elo.winner_delta:+d}</b> / <b>{elo.loser_delta:+d}</b>"
    )

    await safe_render(query, text, get_back_menu())

    for uid in (challenger_tg, opponent_tg):
        try:
            await query.bot.send_message(uid, text, parse_mode="HTML")
        except Exception:
            pass
