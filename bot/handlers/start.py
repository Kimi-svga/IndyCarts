from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_main_menu
from core.config import settings
from core.constants import RESERVED_USERNAMES, USERNAME_PATTERN
from db.session import AsyncSessionLocal
from db.models import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == tg_id)
        user = (await session.execute(stmt)).scalar_one_or_none()

    if user:
        await message.answer(
            f"🏁 С возвращением, <b>{user.username}</b>!\n\n"
            f"💰 Баланс: {user.balance}\n"
            f"🎴 Попытки: {user.daily_attempts}",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\n"
        "Придумай игровой ник.\n\n"
        "<b>Правила:</b>\n"
        "• 3–20 символов\n"
        "• латиница, цифры, _\n"
        "• первый символ — буква\n\n"
        "Введи ник:",
        parse_mode="HTML"
    )


@router.message(F.text.regexp(USERNAME_PATTERN))
async def handle_username(message: Message):
    tg_id = message.from_user.id
    username = message.text.strip()
    username_norm = username.lower()

    if username_norm in RESERVED_USERNAMES:
        await message.answer("❌ Ник зарезервирован.")
        return

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username_normalized == username_norm)
        if (await session.execute(stmt)).scalar_one_or_none():
            await message.answer("❌ Ник занят.")
            return

        user = User(
            telegram_id=tg_id,
            username=username,
            username_normalized=username_norm,
            first_name=message.from_user.first_name or "Игрок",
            balance=settings.DAILY_MONEY,
            daily_attempts=settings.DAILY_ATTEMPTS,
        )
        session.add(user)
        await session.commit()

    await message.answer(
        f"✅ <b>@{username}</b>, ты в игре!\n\n"
        f"💰 {settings.DAILY_MONEY} монет\n"
        f"🎴 {settings.DAILY_ATTEMPTS} попытки на дроп",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🏁 <b>Главное меню</b>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
