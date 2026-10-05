"""Инструменты игрока: /userinfo, /setbalance, /givecard, /resetpvp."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.utils.decorators import check_role
from core.logger import setup_logger
from db.models import Card, User, UserCard
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


async def _require(message: Message, level: str) -> bool:
    if not await check_role(message.from_user.id, level):
        await message.answer("⛔ Нет доступа")
        return False
    return True


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message) -> None:
    if not await _require(message, "moderator"):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/userinfo @username</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        cards_count = (await session.execute(
            select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
        )).scalar() or 0

        collection_value = (await session.execute(
            select(func.sum(Card.current_price))
            .join(UserCard, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )).scalar() or 0

    ban_text = "нет"
    if user.ban_level == "warn":
        ban_text = f"⚠️ {user.warnings_count}/3"
    elif user.ban_level == "mute":
        ban_text = f"🔇 до {user.ban_expires_at.strftime('%d.%m.%Y') if user.ban_expires_at else '—'}"
    elif user.ban_level == "ban":
        ban_text = f"🚫 до {user.ban_expires_at.strftime('%d.%m.%Y') if user.ban_expires_at else 'навсегда'}"

    plus_text = "нет"
    if user.plus_tier == "indy_plus" and user.plus_expires_at:
        from datetime import datetime
        if user.plus_expires_at > datetime.utcnow():
            plus_text = f"💎 до {user.plus_expires_at.strftime('%d.%m.%Y')}"

    text = (
        f"👤 <b>@{user.username}</b> (id: <code>{user.telegram_id}</code>)\n\n"
        f"💰 Баланс: <b>{user.balance:,}</b>\n"
        f"🃏 Карт: <b>{cards_count}</b> · 💎 <b>{collection_value:,}</b>\n"
        f"⚔️ PvP: <b>{user.pvp_rating}</b> · {user.pvp_wins_total}W/{user.pvp_losses_total}L\n"
        f"🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"📊 Trust: <b>{user.trust_score}</b>\n"
        f"💎 Indy+: {plus_text}\n"
        f"🚫 Бан: {ban_text}\n"
        f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("setbalance"))
async def cmd_setbalance(message: Message) -> None:
    if not await _require(message, "owner"):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>/setbalance @username сумма</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        old = user.balance
        user.balance = amount
        await session.commit()
        username = user.username

    await message.answer(
        f"✅ @{username}: {old:,} → <b>{amount:,}</b>",
        parse_mode="HTML",
    )


@router.message(Command("addmoney"))
async def cmd_addmoney(message: Message) -> None:
    if not await _require(message, "owner"):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>/addmoney @username сумма</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()
    try:
        amount = int(parts[2])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        user.balance += amount
        await session.commit()
        username = user.username
        new_balance = user.balance

    await message.answer(
        f"✅ @{username}: +{amount:,} → <b>{new_balance:,}</b>",
        parse_mode="HTML",
    )


@router.message(Command("givecard"))
async def cmd_givecard(message: Message) -> None:
    if not await _require(message, "admin"):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>/givecard @username card_id</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()
    try:
        card_id = int(parts[2])
    except ValueError:
        await message.answer("❌ ID — число")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        card = (await session.execute(
            select(Card).where(Card.id == card_id)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return
        if card is None:
            await message.answer(f"❌ Карта #{card_id} не найдена")
            return

        session.add(UserCard(
            user_id=user.id,
            card_id=card.id,
            acquired_price=0,
        ))
        await session.commit()
        username = user.username
        card_name = card.name
        target_tg = user.telegram_id

    await message.answer(f"✅ @{username} выдана карта: <b>{card_name}</b>", parse_mode="HTML")

    try:
        await message.bot.send_message(
            target_tg,
            f"🎁 <b>Тебе выдана карта:</b> {card_name}",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.message(Command("resetpvp"))
async def cmd_resetpvp(message: Message) -> None:
    if not await _require(message, "admin"):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/resetpvp @username</code>", parse_mode="HTML")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        user.pvp_rating = 1000
        user.pvp_wins = 0
        user.pvp_losses = 0
        await session.commit()
        username = user.username

    await message.answer(f"✅ @{username}: PvP сброшен до 1000")
