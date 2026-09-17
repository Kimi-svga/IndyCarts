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
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
    if user:
        await message.answer(
            f"🏁 С возвращением, <b>{user.username}</b>!\n\n💰 Баланс: {user.balance}\n🎴 Попытки: {user.daily_attempts}",
            reply_markup=get_main_menu(), parse_mode="HTML"
        )
        return
    await message.answer(
        "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\nПридумай игровой ник (3–20 символов, латиница):",
        parse_mode="HTML"
    )

@router.message(F.text.regexp(USERNAME_PATTERN))
async def handle_username(message: Message):
    username = message.text.strip()
    norm = username.lower()
    if norm in RESERVED_USERNAMES:
        await message.answer("❌ Ник зарезервирован.")
        return
    async with AsyncSessionLocal() as session:
        if (await session.execute(select(User).where(User.username_normalized == norm))).scalar_one_or_none():
            await message.answer("❌ Ник занят.")
            return
        session.add(User(
            telegram_id=message.from_user.id, username=username, username_normalized=norm,
            first_name=message.from_user.first_name or "Игрок",
            balance=settings.DAILY_MONEY, daily_attempts=settings.DAILY_ATTEMPTS
        ))
        await session.commit()
    await message.answer(
        f"✅ <b>@{username}</b>, ты в игре!\n\n💰 {settings.DAILY_MONEY} монет\n🎴 {settings.DAILY_ATTEMPTS} попытки",
        reply_markup=get_main_menu(), parse_mode="HTML"
    )

@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text("🏁 <b>Главное меню</b>", reply_markup=get_main_menu(), parse_mode="HTML") 
