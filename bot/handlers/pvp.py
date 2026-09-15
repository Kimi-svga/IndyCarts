from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
import random

from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings
from db.session import AsyncSessionLocal
from db.models import User, UserCard, PvpBattle

router = Router()


@router.callback_query(MainMenu.filter(F.action == "pvp"))
async def cb_pvp(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "⚔️ <b>PvP — Дуэли на кубах</b>\n\n"
        "Вызови игрока:\n<code>/duel @username</code>\n\n"
        f"Стоимость: {settings.PVP_FEE} монет.\n"
        "Победитель забирает случайную карту проигравшего.",
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
        if not challenger or not opponent:
            await message.answer("❌ Игрок не найден")
            return
        if challenger.id == opponent.id:
            await message.answer("❌ Нельзя вызвать себя")
            return
        if challenger.balance < settings.PVP_FEE or opponent.balance < settings.PVP_FEE:
            await message.answer(f"❌ У кого-то нет {settings.PVP_FEE} монет")
            return

        challenger.balance -= settings.PVP_FEE
        opponent.balance -= settings.PVP_FEE

        cr = random.randint(1, 6) + random.randint(1, 6)
        orr = random.randint(1, 6) + random.randint(1, 6)
        winner, loser = (challenger, opponent) if cr > orr else (opponent, challenger)
        wr, lr = (cr, orr) if cr > orr else (orr, cr)

        # Забираем карту у проигравшего
        uc = (await session.execute(select(UserCard).where(UserCard.user_id == loser.id).limit(1))).scalar_one_or_none()
        card_name = "ничего"
        if uc:
            from db.models import Card
            card = (await session.execute(select(Card).where(Card.id == uc.card_id))).scalar_one_or_none()
            card_name = card.name
            uc.user_id = winner.id

        winner.pvp_wins += 1
        loser.pvp_losses += 1
        session.add(PvpBattle(
            challenger_id=challenger.id, opponent_id=opponent.id,
            status="finished", challenger_roll=cr, opponent_roll=orr, winner_id=winner.id,
        ))
        await session.commit()

    await message.answer(
        f"⚔️ <b>Дуэль!</b>\n\n"
        f"🎲 @{challenger.username}: {cr}\n"
        f"🎲 @{opponent.username}: {orr}\n\n"
        f"🏆 Победитель: <b>@{winner.username}</b>\n"
        f"Забирает: {card_name}",
        parse_mode="HTML"
) 
