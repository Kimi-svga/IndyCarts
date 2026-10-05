"""Ban Hammer: /ban, /mute, /warn, /unban, /banlist, /banhistory."""

import re
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.utils.decorators import check_role
from core.config import settings
from core.constants import BAN_LEVELS, BAN_NAMES
from core.logger import setup_logger
from db.models import Ban, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


def parse_duration(text: str) -> tuple[bool, datetime | None]:
    """Парсит строку длительности."""
    text = text.lower().strip()

    if text in ("perm", "forever", "навсегда"):
        return True, None

    m = re.match(r"^(\d+)([dhm])$", text)
    if not m:
        return False, None

    amount = int(m.group(1))
    unit = m.group(2)

    if unit == "m":
        delta = timedelta(minutes=amount)
    elif unit == "h":
        delta = timedelta(hours=amount)
    elif unit == "d":
        delta = timedelta(days=amount)
    else:
        return False, None

    return False, datetime.utcnow() + delta


async def _apply_punishment(
    moderator,
    target_username: str,
    level: str,
    duration_text: str,
    reason: str,
    bot,
) -> str:
    """Применяет наказание."""
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target_username.lower())
        )).scalar_one_or_none()

        if user is None:
            return f"❌ @{target_username} не найден"

        if user.telegram_id in settings.OWNER_IDS:
            return "❌ Нельзя наказать владельца"

        if level == "warn":
            is_perm, expires = False, datetime.utcnow() + timedelta(days=30)
        else:
            is_perm, expires = parse_duration(duration_text)
            if not is_perm and expires is None:
                return "❌ Формат: 30d / 24h / 5m / perm"

        moderator_id = None
        if moderator:
            mod_user = (await session.execute(
                select(User).where(User.telegram_id == moderator.id)
            )).scalar_one_or_none()
            moderator_id = mod_user.id if mod_user else None

        session.add(Ban(
            user_id=user.id,
            level=level,
            reason=reason[:250],
            moderator_id=moderator_id,
            expires_at=expires,
            is_permanent=is_perm,
            is_active=True,
        ))

        if level == "warn":
            user.warnings_count += 1

            if user.warnings_count >= 3:
                user.ban_level = "mute"
                user.ban_expires_at = datetime.utcnow() + timedelta(hours=24)
                user.warnings_count = 0
                note = "\n⚠️ 3 варна → автомьют на 24ч"
            else:
                note = f"\n⚠️ Варнов: {user.warnings_count}/3"
        else:
            user.ban_level = level
            user.ban_expires_at = expires
            if level == "mute":
                user.warnings_count = 0
            note = ""

        await session.commit()

        target_tg = user.telegram_id
        target_name = user.username

    emoji = BAN_LEVELS.get(level, "⚠️")
    name = BAN_NAMES.get(level, level)

    duration_str = "навсегда" if is_perm else (
        expires.strftime("%d.%m.%Y %H:%M") if expires else "—"
    )

    text_to_user = (
        f"{emoji} <b>{name}</b>\n\n"
        f"Причина: {reason}\n"
        f"До: <b>{duration_str}</b>"
    )

    try:
        await bot.send_message(target_tg, text_to_user, parse_mode="HTML")
    except Exception:
        pass

    return (
        f"✅ <b>{name}</b> для @{target_name}\n\n"
        f"Причина: {reason}\n"
        f"До: <b>{duration_str}</b>{note}"
    )


@router.message(Command("ban"))
async def cmd_ban(message: Message) -> None:
    await _cmd_punishment(message, "ban")


@router.message(Command("mute"))
async def cmd_mute(message: Message) -> None:
    await _cmd_punishment(message, "mute")


@router.message(Command("warn"))
async def cmd_warn(message: Message) -> None:
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Формат: <code>/warn @username причина</code>",
            parse_mode="HTML",
        )
        return

    target = parts[1].lstrip("@")
    reason = parts[2]

    if not await check_role(message.from_user.id, "moderator"):
        await message.answer("⛔ Нет доступа")
        return

    result = await _apply_punishment(
        message.from_user, target, "warn", "", reason, message.bot,
    )
    await message.answer(result, parse_mode="HTML")


async def _cmd_punishment(message: Message, level: str) -> None:
    parts = message.text.split(maxsplit=3)
    if len(parts) < 3:
        example = (
            "/ban @user 30d причина\n"
            "/ban @user perm причина\n"
            "/mute @user 24h причина"
        )
        await message.answer(
            f"Формат:\n<code>{example}</code>",
            parse_mode="HTML",
        )
        return

    required = "moderator" if level == "mute" else "admin"
    if not await check_role(message.from_user.id, required):
        await message.answer("⛔ Нет доступа")
        return

    target = parts[1].lstrip("@")

    if len(parts) == 4:
        duration = parts[2]
        reason = parts[3]
    else:
        duration = "24h" if level == "mute" else "30d"
        reason = parts[2]

    result = await _apply_punishment(
        message.from_user, target, level, duration, reason, message.bot,
    )
    await message.answer(result, parse_mode="HTML")


@router.message(Command("unban"))
async def cmd_unban(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/unban @username</code>", parse_mode="HTML")
        return

    if not await check_role(message.from_user.id, "admin"):
        await message.answer("⛔ Нет доступа")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        bans = (await session.execute(
            select(Ban).where(Ban.user_id == user.id, Ban.is_active == True)
        )).scalars().all()

        for b in bans:
            b.is_active = False
            b.lifted_at = datetime.utcnow()
            b.lifted_by = message.from_user.id

        user.ban_level = "none"
        user.ban_expires_at = None
        user.warnings_count = 0

        await session.commit()
        target_tg = user.telegram_id
        username = user.username

    await message.answer(f"✅ @{username} разбанен", parse_mode="HTML")

    try:
        await message.bot.send_message(
            target_tg,
            "✅ <b>Ты разбанен.</b>\n\nСоблюдай правила.",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.message(Command("banlist"))
async def cmd_banlist(message: Message) -> None:
    if not await check_role(message.from_user.id, "moderator"):
        await message.answer("⛔ Нет доступа")
        return

    async with AsyncSessionLocal() as session:
        bans = (await session.execute(
            select(Ban, User)
            .join(User, Ban.user_id == User.id)
            .where(Ban.is_active == True, Ban.level != "warn")
            .order_by(Ban.created_at.desc())
            .limit(20)
        )).all()

    if not bans:
        await message.answer("✅ Активных наказаний нет")
        return

    text = "🚫 <b>Активные наказания</b>\n\n"
    for ban, user in bans:
        emoji = BAN_LEVELS.get(ban.level, "❔")
        dur = "навсегда" if ban.is_permanent else (
            ban.expires_at.strftime("%d.%m.%Y") if ban.expires_at else "—"
        )
        text += f"{emoji} @{user.username} · {dur}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("banhistory"))
async def cmd_banhistory(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Формат: <code>/banhistory @username</code>", parse_mode="HTML")
        return

    if not await check_role(message.from_user.id, "moderator"):
        await message.answer("⛔ Нет доступа")
        return

    target = parts[1].lstrip("@").lower()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.username_normalized == target)
        )).scalar_one_or_none()

        if user is None:
            await message.answer(f"❌ @{target} не найден")
            return

        bans = (await session.execute(
            select(Ban)
            .where(Ban.user_id == user.id)
            .order_by(Ban.created_at.desc())
            .limit(10)
        )).scalars().all()

        username = user.username

    if not bans:
        await message.answer(f"📜 @{username}: наказаний нет")
        return

    text = f"📜 <b>История @{username}</b>\n\n"
    for b in bans:
        emoji = BAN_LEVELS.get(b.level, "❔")
        date = b.created_at.strftime("%d.%m.%Y")
        status = "🟢" if b.is_active else "⚪"
        text += f"{status} {emoji} {date} — {b.reason[:40]}\n"

    await message.answer(text, parse_mode="HTML")
