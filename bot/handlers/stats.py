"""Статистика: /stats, /stats_economy, /stats_cards, /stats_pvp, /stats_plus, /stats_tech."""

from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.utils.decorators import check_role
from core.config import settings
from core.logger import setup_logger
from db.models import (
    Card, DailyStats, Loan, PvpBattle, Subscription, User, UserCard,
)
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


async def _require(message: Message, level: str = "admin") -> bool:
    if not await check_role(message.from_user.id, level):
        await message.answer("⛔ Нет доступа")
        return False
    return True


# ─── /stats ───

@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not await _require(message):
        return

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    async with AsyncSessionLocal() as session:
        users_total = (await session.execute(
            select(func.count(User.id))
        )).scalar() or 0

        users_new = (await session.execute(
            select(func.count(User.id)).where(User.created_at > day_ago)
        )).scalar() or 0

        users_active = (await session.execute(
            select(func.count(User.id)).where(User.updated_at > week_ago)
        )).scalar() or 0

        users_left = (await session.execute(
            select(func.count(User.id)).where(User.updated_at < month_ago)
        )).scalar() or 0

        money_total = (await session.execute(
            select(func.sum(User.balance))
        )).scalar() or 0

        cards_total = (await session.execute(
            select(func.count(UserCard.id))
        )).scalar() or 0

        pvp_day = (await session.execute(
            select(func.count(PvpBattle.id)).where(PvpBattle.created_at > day_ago)
        )).scalar() or 0

        pvp_rating_avg = (await session.execute(
            select(func.avg(User.pvp_rating))
        )).scalar() or 0

        plus_count = (await session.execute(
            select(func.count(User.id)).where(
                User.plus_tier == "indy_plus",
                User.plus_expires_at > now,
            )
        )).scalar() or 0

    plus_percent = (plus_count / users_total * 100) if users_total > 0 else 0

    text = (
        f"📊 <b>Indy Carts · 1.1.0</b>\n\n"
        f"👥 Игроков: <b>{users_total}</b>\n"
        f"📈 Новых за день: <b>{users_new}</b>\n"
        f"🔥 Активных (7д): <b>{users_active}</b>\n"
        f"💀 Ушли (30д): <b>{users_left}</b>\n\n"
        f"💰 Всего монет: <b>{money_total:,}</b>\n"
        f"🃏 Карт в игре: <b>{cards_total}</b>\n\n"
        f"⚔️ PvP за день: <b>{pvp_day}</b>\n"
        f"📊 Средний рейтинг: <b>{int(pvp_rating_avg)}</b>\n\n"
        f"💎 Indy+: <b>{plus_count}</b> ({plus_percent:.1f}%)"
    )

    await message.answer(text, parse_mode="HTML")


# ─── /stats_economy ───

@router.message(Command("stats_economy"))
async def cmd_stats_economy(message: Message) -> None:
    if not await _require(message):
        return

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        money_total = (await session.execute(
            select(func.sum(User.balance))
        )).scalar() or 0

        top = (await session.execute(
            select(User).order_by(User.balance.desc()).limit(5)
        )).scalars().all()

    text = (
        f"💰 <b>Экономика</b>\n\n"
        f"💵 Общий баланс игроков: <b>{money_total:,}</b>\n\n"
        f"🏆 <b>Топ-5 по балансу:</b>\n"
    )
    for i, u in enumerate(top, 1):
        text += f"{i}. @{u.username} — <b>{u.balance:,}</b>\n"

    await message.answer(text, parse_mode="HTML")


# ─── /stats_cards ───

@router.message(Command("stats_cards"))
async def cmd_stats_cards(message: Message) -> None:
    if not await _require(message):
        return

    async with AsyncSessionLocal() as session:
        cards_total = (await session.execute(
            select(func.count(UserCard.id))
        )).scalar() or 0

        iw_count = (await session.execute(
            select(func.count(UserCard.id)).where(UserCard.is_iw == True)
        )).scalar() or 0

        by_rarity = (await session.execute(
            select(Card.rarity, func.count(UserCard.id))
            .join(UserCard, UserCard.card_id == Card.id)
            .group_by(Card.rarity)
        )).all()

    rarity_map = {r: c for r, c in by_rarity}
    from core.constants import RARITY_EMOJI, RARITY_NAMES, RARITIES

    text = (
        f"🃏 <b>Карты</b>\n\n"
        f"Всего в игре: <b>{cards_total}</b>\n"
        f"💎 IW-карт: <b>{iw_count}</b>\n\n"
        f"<b>По редкостям:</b>\n"
    )

    for r in RARITIES:
        count = rarity_map.get(r, 0)
        emoji = RARITY_EMOJI.get(r, "⚪")
        name = RARITY_NAMES.get(r, r)
        text += f"{emoji} {name}: <b>{count}</b>\n"

    await message.answer(text, parse_mode="HTML")


# ─── /stats_pvp ───

@router.message(Command("stats_pvp"))
async def cmd_stats_pvp(message: Message) -> None:
    if not await _require(message):
        return

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    async with AsyncSessionLocal() as session:
        pvp_day = (await session.execute(
            select(func.count(PvpBattle.id)).where(PvpBattle.created_at > day_ago)
        )).scalar() or 0

        pvp_week = (await session.execute(
            select(func.count(PvpBattle.id)).where(PvpBattle.created_at > week_ago)
        )).scalar() or 0

        top = (await session.execute(
            select(User).order_by(User.pvp_rating.desc()).limit(5)
        )).scalars().all()

    text = (
        f"⚔️ <b>PvP</b>\n\n"
        f"📊 За день: <b>{pvp_day}</b> боёв\n"
        f"📈 За неделю: <b>{pvp_week}</b> боёв\n\n"
        f"🏆 <b>Топ-5:</b>\n"
    )
    for i, u in enumerate(top, 1):
        text += (
            f"{i}. @{u.username} — <b>{u.pvp_rating}</b> "
            f"({u.pvp_wins}W/{u.pvp_losses}L)\n"
        )

    await message.answer(text, parse_mode="HTML")


# ─── /stats_plus ───

@router.message(Command("stats_plus"))
async def cmd_stats_plus(message: Message) -> None:
    if not await _require(message):
        return

    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        active = (await session.execute(
            select(func.count(User.id)).where(
                User.plus_tier == "indy_plus",
                User.plus_expires_at > now,
            )
        )).scalar() or 0

        total_stars = (await session.execute(
            select(func.sum(Subscription.total_paid_stars))
        )).scalar() or 0

        total_coins = (await session.execute(
            select(func.sum(Subscription.total_paid_coins))
        )).scalar() or 0

    text = (
        f"💎 <b>Indy+</b>\n\n"
        f"📊 Активных подписок: <b>{active}</b>\n\n"
        f"💰 Заработано:\n"
        f"⭐ Stars: <b>{total_stars}</b>\n"
        f"🪙 Монет: <b>{total_coins:,}</b>"
    )

    await message.answer(text, parse_mode="HTML")


# ─── /stats_tech ───

@router.message(Command("stats_tech"))
async def cmd_stats_tech(message: Message) -> None:
    if not await _require(message):
        return

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        active_loans = (await session.execute(
            select(func.count(Loan.id)).where(Loan.status.in_(["active", "overdue"]))
        )).scalar() or 0

        pvp_pending = (await session.execute(
            select(func.count(PvpBattle.id)).where(PvpBattle.status == "pending")
        )).scalar() or 0

    text = (
        f"⚙️ <b>Техника</b>\n\n"
        f"🏦 Активных кредитов: <b>{active_loans}</b>\n"
        f"⚔️ PvP в очереди: <b>{pvp_pending}</b>\n"
        f"🕒 UTC: {now.strftime('%H:%M:%S')}\n\n"
        f"📅 Cron-задачи — в логах Render"
    )

    await message.answer(text, parse_mode="HTML") 
