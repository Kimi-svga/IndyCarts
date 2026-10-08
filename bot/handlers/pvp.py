"""PvP 2.0: сезоны, мультиставки, автоматические бои."""

import random
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import RARITY_EMOJI, RARITY_NAMES
from core.logger import setup_logger
from db.models import Card, PvpBattle, PvpSeason, PvpStake, User, UserCard
from db.session import AsyncSessionLocal
from services.clan import get_clan_bonuses, get_user_clan
from services.pvp import (
    calculate_elo, calculate_pvp_money_prize, get_rank_title,
)

router = Router()
logger = setup_logger()


class PvpAction(CallbackData, prefix="pvp"):
    """Действие в PvP."""
    action: str
    battle_id: int


class PvpBet(CallbackData, prefix="pvpbet"):
    """Ставка карты."""
    battle_id: int
    user_card_id: int


# ═════════════════════════════════════════════
# МЕНЮ PVP
# ═════════════════════════════════════════════

@router.callback_query(MainMenu.filter(F.action == "pvp"))
async def cb_pvp(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        season = (await session.execute(
            select(PvpSeason).where(PvpSeason.is_active == True)
        )).scalar_one_or_none()

        if user.pvp_blocked_until and user.pvp_blocked_until > datetime.utcnow():
            days_left = (user.pvp_blocked_until - datetime.utcnow()).days
            await safe_render(
                query,
                f"🚫 <b>PvP заблокирован</b>\n\n"
                f"Причина: дефолт по кредиту\n"
                f"До: <b>{user.pvp_blocked_until.strftime('%d.%m.%Y')}</b>\n"
                f"Осталось: <b>{days_left} дней</b>",
                get_back_menu(),
            )
            return

        # Клановый бонус PvP
        clan, _ = await get_user_clan(session, user.id)
        clan_line = ""
        if clan is not None:
            bonuses = get_clan_bonuses(clan.level)
            pvp_bonus = bonuses.auction_discount / 10  # 0.0–0.5
            if pvp_bonus > 0:
                clan_line = f"\n🏰 <b>Клан-бонус PvP:</b> +{pvp_bonus * 100:.0f}%"

    title = get_rank_title(user.pvp_rating)
    season_text = "не активен"
    if season:
        days_left = (season.ends_at - datetime.utcnow()).days
        season_text = f"S{season.number} · {days_left} дней"

    text = (
        f"⚔️ <b>PvP Кубы</b>\n\n"
        f"📊 Рейтинг: <b>{user.pvp_rating}</b>\n"
        f"🏅 Титул: {title}\n"
        f"📈 Сезон: <b>{season_text}</b>\n"
        f"📊 Всего: <b>{user.pvp_wins_total}W / {user.pvp_losses_total}L</b>"
        f"{clan_line}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Ставка:</b> до {settings.PVP_MAX_STAKES_PER_SIDE} карт с каждой стороны\n"
        f"<b>Деньги:</b> {settings.PVP_FEE} монет с каждого\n"
        f"<b>Комиссия игры:</b> {int(settings.PVP_BANK_COMMISSION * 100)}%\n\n"
        f"Вызови игрока: <code>/duel @username</code>"
    )

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


# ═════════════════════════════════════════════
# ВЫЗОВ НА ДУЭЛЬ
# ═════════════════════════════════════════════

@router.message(Command("duel"))
async def cmd_duel(message: Message) -> None:
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

        if challenger.pvp_blocked_until and challenger.pvp_blocked_until > datetime.utcnow():
            await message.answer("🚫 Ты в PvP-блоке")
            return

        if challenger.balance < settings.PVP_FEE:
            await message.answer(f"❌ Нужно {settings.PVP_FEE} монет")
            return

        season = (await session.execute(
            select(PvpSeason).where(PvpSeason.is_active == True)
        )).scalar_one_or_none()

        battle = PvpBattle(
            challenger_id=challenger.id,
            opponent_id=opponent.id,
            status="pending",
            money_stake=settings.PVP_FEE,
            season_id=season.id if season else None,
        )
        session.add(battle)
        await session.commit()
        await session.refresh(battle)
        battle_id = battle.id
        opponent_tg = opponent.telegram_id
        challenger_name = challenger.username

    b_opp = InlineKeyboardBuilder()
    b_opp.button(
        text="✅ Принять",
        callback_data=PvpAction(action="choose", battle_id=battle_id).pack(),
    )
    b_opp.button(
        text="❌ Отклонить",
        callback_data=PvpAction(action="decline", battle_id=battle_id).pack(),
    )
    b_opp.adjust(2)

    try:
        await message.bot.send_message(
            opponent_tg,
            f"⚔️ <b>Вызов на PvP!</b>\n\n"
            f"От: <b>@{challenger_name}</b>\n\n"
            f"Принять вызов?",
            reply_markup=b_opp.as_markup(),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Не удалось отправить вызов: {e}")
        await message.answer("❌ Не удалось отправить вызов")
        return

    b_ch = InlineKeyboardBuilder()
    b_ch.button(
        text="🎴 Выбрать свои карты",
        callback_data=PvpAction(action="choose", battle_id=battle_id).pack(),
    )
    b_ch.adjust(1)

    await message.answer(
        f"⚔️ <b>Вызов отправлен @{target}</b>\n\n"
        f"Пока противник думает — выбери свои карты.",
        reply_markup=b_ch.as_markup(),
        parse_mode="HTML",
    )


# ═════════════════════════════════════════════
# ОТКЛОНЕНИЕ
# ═════════════════════════════════════════════

@router.callback_query(PvpAction.filter(F.action == "decline"))
async def cb_pvp_decline(query: CallbackQuery, callback_data: PvpAction) -> None:
    await safe_answer(query, "❌ Отклонено")

    challenger_tg = None

    async with AsyncSessionLocal() as session:
        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == callback_data.battle_id)
        )).scalar_one_or_none()

        if battle:
            battle.status = "declined"

            stakes = (await session.execute(
                select(PvpStake).where(PvpStake.battle_id == battle.id)
            )).scalars().all()
            for stake in stakes:
                uc = await session.get(UserCard, stake.user_card_id)
                if uc:
                    uc.is_locked = False

            await session.commit()

            challenger = await session.get(User, battle.challenger_id)
            challenger_tg = challenger.telegram_id if challenger else None

    await safe_render(query, "❌ Вызов отклонён.", get_back_menu())

    if challenger_tg:
        try:
            await query.bot.send_message(
                challenger_tg,
                f"❌ <b>@{query.from_user.username}</b> отклонил вызов.",
                parse_mode="HTML",
            )
        except Exception:
            pass


# ═════════════════════════════════════════════
# ВЫБОР КАРТ
# ═════════════════════════════════════════════

@router.callback_query(PvpAction.filter(F.action == "choose"))
async def cb_pvp_choose(query: CallbackQuery, callback_data: PvpAction) -> None:
    await safe_answer(query)
    await _show_card_picker(query, callback_data.battle_id, 0)


async def _show_card_picker(query: CallbackQuery, battle_id: int, index: int) -> None:
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == battle_id)
        )).scalar_one_or_none()

        if battle is None:
            await safe_render(query, "❌ Бой не найден", get_back_menu())
            return

        if user.id not in (battle.challenger_id, battle.opponent_id):
            await safe_render(query, "❌ Ты не участник боя", get_back_menu())
            return

        if battle.status != "pending":
            await safe_render(query, "❌ Бой уже завершён", get_back_menu())
            return

        stmt = (
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(
                UserCard.user_id == user.id,
                UserCard.is_locked == False,
            )
            .order_by(Card.current_price.desc())
            .limit(20)
        )
        rows = (await session.execute(stmt)).all()

        chosen = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle_id,
                PvpStake.user_id == user.id,
            )
        )).scalars().all()
        chosen_ids = {s.user_card_id for s in chosen}

    if not rows:
        await safe_render(query, "❌ Нет доступных карт", get_back_menu())
        return

    if index < 0 or index >= len(rows):
        index = 0

    user_card, card = rows[index]
    emoji = RARITY_EMOJI.get(card.rarity, "⚪")
    is_chosen = user_card.id in chosen_ids
    mark = " ✅" if is_chosen else ""

    text = (
        f"🎁 <b>Выбери карты для ставки</b>\n\n"
        f"{emoji} <b>{card.name}</b>{mark}\n"
        f"Редкость: {RARITY_NAMES[card.rarity]}\n"
        f"Цена: <b>{card.current_price:,}</b>\n\n"
        f"Карта <b>{index + 1}</b> из <b>{len(rows)}</b>\n"
        f"Выбрано: <b>{len(chosen_ids)}/{settings.PVP_MAX_STAKES_PER_SIDE}</b>"
    )

    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=f"pvpnav_{battle_id}_{index - 1}")
    b.button(text=f"{index + 1}/{len(rows)}", callback_data="noop")
    if index < len(rows) - 1:
        b.button(text="➡️", callback_data=f"pvpnav_{battle_id}_{index + 1}")

    if is_chosen:
        b.button(text="➖ Убрать", callback_data=f"pvptog_{battle_id}_{user_card.id}")
    else:
        b.button(text="➕ Поставить", callback_data=f"pvptog_{battle_id}_{user_card.id}")

    b.button(
        text="✅ Готов",
        callback_data=PvpAction(action="ready", battle_id=battle_id).pack(),
    )
    b.button(
        text="🔙 Отмена",
        callback_data=PvpAction(action="decline", battle_id=battle_id).pack(),
    )
    b.adjust(3, 1, 1, 1)

    await safe_render(query, text, b.as_markup(), photo_file_id=card.image_file_id)


@router.callback_query(F.data.startswith("pvpnav_"))
async def cb_pvp_nav(query: CallbackQuery) -> None:
    await safe_answer(query)
    _, battle_id, index = query.data.split("_")
    await _show_card_picker(query, int(battle_id), int(index))


@router.callback_query(F.data.startswith("pvptog_"))
async def cb_pvp_toggle(query: CallbackQuery) -> None:
    await safe_answer(query)
    _, battle_id, user_card_id = query.data.split("_")
    battle_id = int(battle_id)
    user_card_id = int(user_card_id)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        battle = await session.get(PvpBattle, battle_id)
        if battle is None or battle.status != "pending":
            return

        side = "challenger" if battle.challenger_id == user.id else "opponent"

        existing = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle_id,
                PvpStake.user_card_id == user_card_id,
            )
        )).scalar_one_or_none()

        if existing:
            await session.delete(existing)
            uc = await session.get(UserCard, user_card_id)
            if uc:
                uc.is_locked = False
        else:
            count = (await session.execute(
                select(PvpStake).where(
                    PvpStake.battle_id == battle_id,
                    PvpStake.user_id == user.id,
                )
            )).scalars().all()

            if len(count) >= settings.PVP_MAX_STAKES_PER_SIDE:
                await safe_answer(
                    query,
                    f"❌ Максимум {settings.PVP_MAX_STAKES_PER_SIDE} карт",
                    show_alert=True,
                )
                return

            uc = (await session.execute(
                select(UserCard).where(
                    UserCard.id == user_card_id,
                    UserCard.user_id == user.id,
                )
            )).scalar_one_or_none()

            if uc is None:
                await safe_answer(query, "❌ Карта не найдена", show_alert=True)
                return

            uc.is_locked = True
            session.add(PvpStake(
                battle_id=battle_id,
                user_id=user.id,
                user_card_id=user_card_id,
                side=side,
            ))

        await session.commit()

    await _show_card_picker(query, battle_id, 0)


# ═════════════════════════════════════════════
# ГОТОВНОСТЬ
# ═════════════════════════════════════════════

@router.callback_query(PvpAction.filter(F.action == "ready"))
async def cb_pvp_ready(query: CallbackQuery, callback_data: PvpAction) -> None:
    await safe_answer(query)
    battle_id = callback_data.battle_id

    should_run = False

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == battle_id)
        )).scalar_one_or_none()

        if battle is None or battle.status != "pending":
            await safe_render(query, "❌ Вызов неактуален", get_back_menu())
            return

        side = "challenger" if battle.challenger_id == user.id else "opponent"

        stakes = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle_id,
                PvpStake.user_id == user.id,
            )
        )).scalars().all()

        if not stakes:
            await safe_answer(query, "❌ Выбери хотя бы 1 карту", show_alert=True)
            return

        if side == "challenger":
            battle.challenger_ready = True
        else:
            battle.opponent_ready = True

        if battle.challenger_ready and battle.opponent_ready:
            should_run = True

        await session.commit()

        if not should_run:
            await safe_render(
                query,
                "✅ <b>Ты готов!</b>\n\n⏳ Ждём противника...",
                get_back_menu(),
            )
            return

    if should_run:
        await safe_render(
            query,
            "⚔️ <b>Бой начинается!</b>\n\nСмотри результат...",
            get_back_menu(),
        )
        await _run_battle_async(battle_id, query.bot)


# ═════════════════════════════════════════════
# АВТОМАТИЧЕСКИЙ БОЙ (с клановым бонусом)
# ═════════════════════════════════════════════

async def _run_battle_async(battle_id: int, bot) -> None:
    async with AsyncSessionLocal() as session:
        battle = (await session.execute(
            select(PvpBattle).where(PvpBattle.id == battle_id)
        )).scalar_one_or_none()

        if battle is None or battle.status != "pending":
            return

        challenger = await session.get(User, battle.challenger_id)
        opponent = await session.get(User, battle.opponent_id)

        if challenger is None or opponent is None:
            return

        cr = random.randint(1, 6) + random.randint(1, 6)
        orr = random.randint(1, 6) + random.randint(1, 6)
        while cr == orr:
            cr = random.randint(1, 6) + random.randint(1, 6)
            orr = random.randint(1, 6) + random.randint(1, 6)

        winner, loser = (challenger, opponent) if cr > orr else (opponent, challenger)

        elo = calculate_elo(winner.pvp_rating, loser.pvp_rating)
        winner_delta = elo.winner_delta
        loser_delta = elo.loser_delta

        # Indy+ множитель
        if winner.plus_tier == "indy_plus":
            winner_delta = int(winner_delta * settings.PLUS_PVP_MULTIPLIER)
        if loser.plus_tier == "indy_plus":
            loser_delta = int(loser_delta / settings.PLUS_PVP_MULTIPLIER)

        # ─── КЛАНОВЫЙ МНОЖИТЕЛЬ ───
        winner_clan, _ = await get_user_clan(session, winner.id)
        loser_clan, _ = await get_user_clan(session, loser.id)

        if winner_clan is not None:
            wb = get_clan_bonuses(winner_clan.level)
            pvp_bonus = wb.auction_discount / 10  # 0.0–0.5
            if pvp_bonus > 0:
                winner_delta = int(winner_delta * (1 + pvp_bonus))

        if loser_clan is not None:
            lb = get_clan_bonuses(loser_clan.level)
            pvp_shield = lb.auction_discount / 10
            if pvp_shield > 0:
                loser_delta = int(loser_delta / (1 + pvp_shield))

        winner.pvp_rating += winner_delta
        loser.pvp_rating += loser_delta
        if loser.pvp_rating < 100:
            loser.pvp_rating = 100

        winner.pvp_wins += 1
        winner.pvp_wins_total += 1
        loser.pvp_losses += 1
        loser.pvp_losses_total += 1

        loser_side = "challenger" if loser.id == battle.challenger_id else "opponent"
        loser_stakes = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle.id,
                PvpStake.side == loser_side,
            )
        )).scalars().all()

        cards_transferred = 0
        for stake in loser_stakes:
            uc = await session.get(UserCard, stake.user_card_id)
            if uc:
                uc.user_id = winner.id
                uc.is_locked = False
                cards_transferred += 1

        winner_side = "challenger" if winner.id == battle.challenger_id else "opponent"
        winner_stakes = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle.id,
                PvpStake.side == winner_side,
            )
        )).scalars().all()

        for stake in winner_stakes:
            uc = await session.get(UserCard, stake.user_card_id)
            if uc:
                uc.is_locked = False

        money_prize = calculate_pvp_money_prize(
            battle.money_stake, battle.money_stake,
            commission=settings.PVP_BANK_COMMISSION,
        )
        winner.balance += money_prize
        loser.balance -= battle.money_stake

        winner.pvp_money_won += money_prize
        winner.pvp_money_staked += battle.money_stake
        loser.pvp_money_staked += battle.money_stake

        battle.status = "finished"
        battle.challenger_roll = cr
        battle.opponent_roll = orr
        battle.winner_id = winner.id
        battle.finished_at = datetime.utcnow()

        c_name = challenger.username
        o_name = opponent.username
        w_name = winner.username
        challenger_tg = challenger.telegram_id
        opponent_tg = opponent.telegram_id

        await session.commit()

    result_text = (
        f"⚔️ <b>Дуэль завершена!</b>\n\n"
        f"🎲 @{c_name}: <b>{cr}</b>\n"
        f"🎲 @{o_name}: <b>{orr}</b>\n\n"
        f"🏆 Победитель: <b>@{w_name}</b>\n"
        f"🃏 Забрал карт: <b>{cards_transferred}</b>\n"
        f"💰 Выиграл: <b>+{money_prize}</b> монет\n"
        f"📈 Рейтинг: <b>+{winner_delta}</b> / <b>{loser_delta}</b>"
    )

    for uid in (challenger_tg, opponent_tg):
        try:
            await bot.send_message(uid, result_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить результат боя: {e}")


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery) -> None:
    await safe_answer(query)
