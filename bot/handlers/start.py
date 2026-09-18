from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_main_menu
from core.config import settings
from core.constants import RESERVED_USERNAMES, USERNAME_PATTERN
from db.session import AsyncSessionLocal
from db.models import User

router = Router()
CHANNEL_ID = "@IndyCarts"


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/IndyCarts")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not await is_subscribed(message.bot, message.from_user.id):
        await message.answer(
            "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\nЧтобы начать играть, подпишись на наш канал:\n📢 @IndyCarts\n\nПосле подписки нажми «✅ Я подписался»",
            reply_markup=subscribe_keyboard(),
            parse_mode="HTML"
        )
        return
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
    if user:
        await message.answer(
            f"🏁 С возвращением, <b>{user.username}</b>!\n\n💰 Баланс: {user.balance}\n🎴 Попытки: {user.daily_attempts}",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        return
    await message.answer(
        "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\nПридумай игровой ник (3–20 символов, латиница):",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(query: CallbackQuery):
    await query.answer()
    if not await is_subscribed(query.bot, query.from_user.id):
        await query.answer("❌ Ты ещё не подписан!", show_alert=True)
        return
    await query.message.edit_text(
        "✅ <b>Подписка подтверждена!</b>\n\nТеперь можешь играть.\n\nПридумай игровой ник (3–20 символов, латиница):",
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
            telegram_id=message.from_user.id,
            username=username,
            username_normalized=norm,
            first_name=message.from_user.first_name or "Игрок",
            balance=settings.DAILY_MONEY,
            daily_attempts=settings.DAILY_ATTEMPTS
        ))
        await session.commit()
    await message.answer(
        f"✅ <b>@{username}</b>, ты в игре!\n\n💰 {settings.DAILY_MONEY} монет\n🎴 {settings.DAILY_ATTEMPTS} попытки",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text("🏁 <b>Главное меню</b>", reply_markup=get_main_menu(), parse_mode="HTML")
