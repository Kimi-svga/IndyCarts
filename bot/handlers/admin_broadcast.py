"""Массовые: /broadcast_plus, /broadcast_top, /announce, /giveaway."""

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from bot.utils.decorators import check_role
from core.logger import setup_logger
from db.models import User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()


class BroadcastState(StatesGroup):
    content = State()


async def _require(message: Message, level: str = "admin") -> bool:
    if not await check_role(message.from_user.id, level):
        await message.answer("⛔ Нет доступа")
        return False
    return True


# ─── /broadcast_plus ───

@router.message(Command("broadcast_plus"))
async def cmd_broadcast_plus(message: Message, state: FSMContext) -> None:
    if not await _require(message):
        return
    await state.set_state(BroadcastState.content)
    await state.update_data(segment="plus")
    await message.answer("📨 Отправь текст или фото для Indy+ подписчиков.")


# ─── /broadcast_top ───

@router.message(Command("broadcast_top"))
async def cmd_broadcast_top(message: Message, state: FSMContext) -> None:
    if not await _require(message):
        return
    await state.set_state(BroadcastState.content)
    await state.update_data(segment="top")
    await message.answer("📨 Отправь текст или фото для топ-10 по PvP.")


# ─── Обработчик контента ───

@router.message(BroadcastState.content)
async def handle_broadcast(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    segment = data.get("segment", "all")
    await state.clear()

    now = datetime.utcnow()
    async with AsyncSessionLocal() as session:
        if segment == "plus":
            users = (await session.execute(
                select(User.telegram_id).where(
                    User.plus_tier == "indy_plus",
                    User.plus_expires_at > now,
                )
            )).scalars().all()
        elif segment == "top":
            users = (await session.execute(
                select(User.telegram_id).order_by(User.pvp_rating.desc()).limit(10)
            )).scalars().all()
        else:
            users = (await session.execute(select(User.telegram_id))).scalars().all()

    await message.answer(f"⏳ Рассылка для {len(users)}...")

    count = 0
    for uid in users:
        try:
            if message.photo:
                await message.bot.send_photo(
                    uid, message.photo[-1].file_id,
                    caption=message.caption or "",
                    parse_mode="HTML",
                )
            else:
                await message.bot.send_message(uid, message.text, parse_mode="HTML")
            count += 1
        except Exception:
            pass

    await message.answer(f"✅ Отправлено: {count}/{len(users)}")


# ─── /announce ───

@router.message(Command("announce"))
async def cmd_announce(message: Message) -> None:
    if not await _require(message, "admin"):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: <code>/announce текст</code>", parse_mode="HTML")
        return

    try:
        await message.bot.send_message(
            "@IndyCarts",
            parts[1],
            parse_mode="HTML",
        )
        await message.answer("✅ Опубликовано в канал")
    except Exception as e:
        await message.answer(f"❌ Не удалось: {e}")


# ─── /giveaway ───

@router.message(Command("giveaway"))
async def cmd_giveaway(message: Message) -> None:
    if not await _require(message, "owner"):
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: <code>/giveaway @username сумма</code>", parse_mode="HTML")
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
        target_tg = user.telegram_id

    await message.answer(
        f"✅ @{username}: +{amount:,} → <b>{new_balance:,}</b>",
        parse_mode="HTML",
    )

    try:
        await message.bot.send_message(
            target_tg,
            f"🎁 <b>Тебе подарок!</b>\n\n+{amount:,} монет",
            parse_mode="HTML",
        )
    except Exception:
        pass
