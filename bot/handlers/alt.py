"""Альт-аккаунты для админов (бета)."""

import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from core.config import settings
from core.constants import RESERVED_USERNAMES, USERNAME_PATTERN
from core.logger import setup_logger
from db.models import AltAccount, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()

MAX_ALTS = 5


@router.message(Command("alt"))
async def cmd_alt(message: Message) -> None:
    if message.from_user.id not in settings.OWNER_IDS and message.from_user.id not in settings.ADMIN_IDS:
        return

    parts = message.text.split()
    action = parts[1].lower() if len(parts) > 1 else None

    if action == "create":
        if len(parts) < 3:
            await message.answer("Формат: <code>/alt create username</code>", parse_mode="HTML")
            return

        username = parts[2].strip().lstrip("@")
        username_norm = username.lower()

        if not re.match(USERNAME_PATTERN, username):
            await message.answer("❌ Ник: 3–20 символов, латиница", parse_mode="HTML")
            return

        if username_norm in RESERVED_USERNAMES:
            await message.answer("❌ Ник зарезервирован", parse_mode="HTML")
            return

        async with AsyncSessionLocal() as session:
            main = (await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )).scalar_one_or_none()

            if not main:
                await message.answer("❌ Сначала /start")
                return

            existing_nick = (await session.execute(
                select(User).where(User.username_normalized == username_norm)
            )).scalar_one_or_none()

            if existing_nick:
                await message.answer("❌ Ник занят", parse_mode="HTML")
                return

            # Считаем, сколько уже альтов
            existing_alts = (await session.execute(
                select(AltAccount).where(AltAccount.main_user_id == main.id)
            )).scalars().all()

            if len(existing_alts) >= MAX_ALTS:
                await message.answer(f"❌ Максимум {MAX_ALTS} альтов", parse_mode="HTML")
                return

            # Создаём фейковый telegram_id для альта
            fake_id = -(main.telegram_id + 1_000_000_000 + len(existing_alts) + 1)
            
            alt = User(
                telegram_id=fake_id,
                username=username,
                username_normalized=username_norm,
                first_name="Test Alt",
                balance=0,
                daily_attempts=0,
            )
            session.add(alt)
            await session.flush()

            session.add(AltAccount(main_user_id=main.id, alt_user_id=alt.id))
            await session.commit()

            await message.answer(
                f"✅ <b>Альт создан</b>\n\n"
                f"🎮 @{username}\n"
                f"💰 0 монет\n"
                f"🃏 0 попыток\n\n"
                f"▶️ Войти: <code>/alt switch {username}</code>",
                parse_mode="HTML",
            )

    elif action == "switch":
        if len(parts) < 3:
            await message.answer("Формат: <code>/alt switch username</code>", parse_mode="HTML")
            return

        username = parts[2].strip().lstrip("@").lower()

        async with AsyncSessionLocal() as session:
            main = (await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )).scalar_one_or_none()

            if not main:
                return

            alts = (await session.execute(
                select(AltAccount, User)
                .join(User, AltAccount.alt_user_id == User.id)
                .where(AltAccount.main_user_id == main.id)
            )).all()

            target = None
            for link, alt in alts:
                if alt.username_normalized == username:
                    target = alt
                    break

            if not target:
                await message.answer("❌ Альт не найден", parse_mode="HTML")
                return

            if main.active_alt_id == target.id:
                await message.answer(f"⚠️ Ты уже играешь за @{target.username}", parse_mode="HTML")
                return

            main.active_alt_id = target.id
            await session.commit()

            await message.answer(
                f"🎮 <b>Ты вошёл как @{target.username}</b>\n\n"
                f"💰 {target.balance:,} монет\n"
                f"🃏 {target.daily_attempts} попыток\n\n"
                f"Все команды теперь работают на этого альта.\n"
                f"Вернуться: /alt main",
                parse_mode="HTML",
            )

    elif action == "main":
        async with AsyncSessionLocal() as session:
            main = (await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )).scalar_one_or_none()

            if main:
                if main.active_alt_id is None:
                    await message.answer("⚠️ Ты уже на основном аккаунте", parse_mode="HTML")
                    return
                    
                main.active_alt_id = None
                await session.commit()
                await message.answer(
                    f"🏠 <b>Ты вернулся на основной</b>\n\n"
                    f"👤 @{main.username}\n"
                    f"💰 {main.balance:,} монет",
                    parse_mode="HTML",
                )

    elif action == "list":
        async with AsyncSessionLocal() as session:
            main = (await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )).scalar_one_or_none()

            if not main:
                return

            alts = (await session.execute(
                select(AltAccount, User)
                .join(User, AltAccount.alt_user_id == User.id)
                .where(AltAccount.main_user_id == main.id)
            )).all()

            if not alts:
                await message.answer("📋 У тебя нет альтов", parse_mode="HTML")
                return

            text = f"👥 <b>Твои альты ({len(alts)}/{MAX_ALTS})</b>\n\n"
            for link, alt in alts:
                mark = " ◀ <b>активный</b>" if main.active_alt_id == alt.id else ""
                text += f"🎮 <b>@{alt.username}</b>{mark}\n"
                text += f"    💰 {alt.balance:,} · 🃏 {alt.daily_attempts}\n\n"

            await message.answer(text, parse_mode="HTML")

    else:
        await message.answer(
            "👥 <b>Альт-аккаунты (бета)</b>\n\n"
            "<code>/alt create username</code> — создать\n"
            "<code>/alt switch username</code> — войти\n"
            "<code>/alt main</code> — вернуться\n"
            "<code>/alt list</code> — список",
            parse_mode="HTML"
) 
