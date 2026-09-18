from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
import random

from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings
from core.constants import RARITY_EMOJI, RARITY_NAMES
from db.session import AsyncSessionLocal
from db.models import User, UserCard, PvpBattle, Card

router = Router()


class PvpAction(CallbackData, prefix="pvp"):
    action: str
    battle_id: int


class PvpBet(CallbackData, prefix="pvpbet"):
    battle_id: int
    user_card_id: int


@router.callback_query(MainMenu.filter(F.action == "pvp"))
async def cb_pvp(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        f"⚔️ <b>PvP — Дуэли на кубах</b>\n\nВызови игрока:\n<code>/duel @username</code>\n\nСтоимость: {settings.PVP_FEE} монет\nПобедитель забирает карту проигравшего.",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
    )


@router.message(F.text.startswith("/duel"))
async def cmd_duel(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/duel @username</code>", parse_mode="HTML")
        return
    target = parts[1].lstrip("@").lower()
    async with AsyncSessionLocal() as session:
        challenger = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        opponent = (await session.execute(select(User).where(User.username_normalized == target))).scalar_one_or_none()
        if not challenger:
            await message.answer("❌ Сначала /start")
            return
        if not opponent:
            await message.answer("❌ Игрок не найден")
            return
        if challenger.id == opponent.id:
            await message.answer("❌ Нельзя вызвать себя")
            return
        if challenger.balance < settings.PVP_FEE:
            await message.answer(f"❌ Нужно {settings.PVP_FEE} монет")
            return
        battle = PvpBattle(challenger_id=challenger.id, opponent_id=opponent.id, status="pending")
        session.add(battle)
        await session.commit()
        battle_id = battle.id
        opponent_tg = opponent.telegram_id
        challenger_name = challenger.username

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять", callback_data=PvpAction(action="choose_card", battle_id=battle_id))
    builder.button(text="❌ Отклонить", callback_data=PvpAction(action="decline", battle_id=battle_id))
    builder.adjust(2)

    try:
        await message.bot.send_message(
            opponent_tg,
            f"⚔️ <b>Вызов на PvP!</b>\n\nОт: <b>@{challenger_name}</b>\n\nСтоимость: {settings.PVP_FEE} монет\nПобедитель забирает карту.\n\nПринять?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        await message.answer("❌ Не удалось отправить вызов")
    await message.answer(f"⚔️ Вызов отправлен @{target}!")


@router.callback_query(PvpAction.filter(F.action == "decline"))
async def cb_pvp_decline(query: CallbackQuery, callback_data: PvpAction):
    await query.answer("❌ Вызов отклонён")
    async with AsyncSessionLocal() as session:
        battle = (await session.execute(select(PvpBattle).where(PvpBattle.id == callback_data.battle_id))).scalar_one_or_none()
        if battle:
            battle.status = "declined"
            await session.commit()
            challenger = (await session.execute(select(User).where(User.id == battle.challenger_id))).scalar_one_or_none()
            challenger_tg = challenger.telegram_id
            opponent_name = query.from_user.username
    await query.message.edit_text("❌ Вызов отклонён.", reply_markup=get_back_menu())
    try:
        await query.bot.send_message(challenger_tg, f"❌ <b>@{opponent_name}</b> отклонил вызов.", parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(PvpAction.filter(F.action == "choose_card"))
async def cb_pvp_choose_card(query: CallbackQuery, callback_data: PvpAction):
    await query.answer()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            return
        stmt = select(UserCard, Card).join(Card, UserCard.card_id == Card.id).where(UserCard.user_id == user.id)
        rows = (await session.execute(stmt)).all()
    if not rows:
        await query.answer("❌ У тебя нет карт", show_alert=True)
        return
    await show_card_for_bet(query, rows, 0, callback_data.battle_id)


async def show_card_for_bet(query: CallbackQuery, rows: list, index: int, battle_id: int):
    uc, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    text = (
        f"🎁 <b>Выбери карту для ставки</b>\n\n"
        f"{emoji} <b>{card.name}</b>\nРедкость: {RARITY_NAMES[card.rarity]}\nЦена: {card.current_price}\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(rows)}</b>"
    )
    builder = InlineKeyboardBuilder()
    if index > 0:
        builder.button(text="⬅️", callback_data=f"betnav_{battle_id}_{index - 1}")
    builder.button(text=f"{index + 1}/{len(rows)}", callback_data="noop")
    if index < len(rows) - 1:
        builder.button(text="➡️", callback_data=f"betnav_{battle_id}_{index + 1}")
    builder.button(text="✅ Поставить эту", callback_data=PvpBet(battle_id=battle_id, user_card_id=uc.id))
    builder.button(text="🔙 Назад", callback_data=PvpAction(action="decline", battle_id=battle_id))
    builder.adjust(3, 1, 1)
    try:
        await query.message.delete()
    except Exception:
        pass
    if card.image_file_id:
        await query.message.answer_photo(card.image_file_id, caption=text, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await query.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("betnav_"))
async def cb_bet_nav(query: CallbackQuery):
    await query.answer()
    _, battle_id, index = query.data.split("_")
    battle_id = int(battle_id)
    index = int(index)
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        stmt = select(UserCard, Card).join(Card, UserCard.card_id == Card.id).where(UserCard.user_id == user.id)
        rows = (await session.execute(stmt)).all()
    await show_card_for_bet(query, rows, index, battle_id)


@router.callback_query(PvpBet.filter())
async def cb_pvp_bet_confirm(query: CallbackQuery, callback_data: PvpBet):
    await query.answer()
    await _finish_pvp(query, callback_data.battle_id, callback_data.user_card_id)


async def _finish_pvp(query: CallbackQuery, battle_id: int, chosen_card_id: int | None):
    async with AsyncSessionLocal() as session:
        battle = (await session.execute(select(PvpBattle).where(PvpBattle.id == battle_id))).scalar_one_or_none()
        if not battle or battle.status != "pending":
            await query.answer("❌ Вызов уже неактуален", show_alert=True)
            return
        challenger = (await session.execute(select(User).where(User.id == battle.challenger_id))).scalar_one_or_none()
        opponent = (await session.execute(select(User).where(User.id == battle.opponent_id))).scalar_one_or_none()
        if challenger.balance < settings.PVP_FEE or opponent.balance < settings.PVP_FEE:
            await query.answer(f"❌ У кого-то нет {settings.PVP_FEE} монет", show_alert=True)
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
        card_name = "ничего"
        if chosen_card_id:
            uc = (await session.execute(select(UserCard).where(UserCard.id == chosen_card_id, UserCard.user_id == loser.id))).scalar_one_or_none()
        else:
            uc = (await session.execute(select(UserCard).where(UserCard.user_id == loser.id).limit(1))).scalar_one_or_none()
        if uc:
            card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
            card_name = card.name
            uc.user_id = winner.id
        winner.pvp_wins += 1
        loser.pvp_losses += 1
        battle.status = "finished"
        battle.challenger_roll = cr
        battle.opponent_roll = orr
        battle.winner_id = winner.id
        await session.commit()
        c_name, o_name, w_name = challenger.username, opponent.username, winner.username
        challenger_tg = challenger.telegram_id
        opponent_tg = opponent.telegram_id
    text = (
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"🎲 @{c_name}: {cr}\n🎲 @{o_name}: {orr}\n\n"
        f"🏆 Победитель: <b>@{w_name}</b>\nЗабирает: {card_name}"
    )
    await query.message.edit_text(text, parse_mode="HTML")
    for uid in [challenger_tg, opponent_tg]:
        try:
            await query.bot.send_message(uid, text, parse_mode="HTML")
        except Exception:
            pass 
