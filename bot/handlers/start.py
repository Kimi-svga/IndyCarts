from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_main_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import RESERVED_USERNAMES, USERNAME_PATTERN
from db.session import AsyncSessionLocal
from db.models import User

router = Router()
CHANNEL_ID = "@IndyCarts"


class RegState(StatesGroup):
    waiting_username = State()


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
async def cmd_start(message: Message, state: FSMContext):
    if not await is_subscribed(message.bot, message.from_user.id):
        await message.answer(
            "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\n"
            "Чтобы начать, подпишись на канал:\n📢 @IndyCarts\n\n"
            "Потом нажми «✅ Я подписался»",
            reply_markup=subscribe_keyboard(),
            parse_mode="HTML"
        )
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()

    if user:
        await message.answer(
            f"🏁 С возвращением, <b>{user.username}</b>!\n\n"
            f"💰 Баланс: {user.balance}\n🎴 Попытки: {user.daily_attempts}",
            reply_markup=get_main_menu(is_owner=message.from_user.id in settings.OWNER_IDS),
            parse_mode="HTML"
        )
        return

    await state.set_state(RegState.waiting_username)
    await message.answer(
        "🏁 <b>Добро пожаловать!</b>\n\n"
        "Придумай игровой ник (3–20 символов, латиница):",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(query: CallbackQuery, state: FSMContext):
    await safe_answer(query)
    if not await is_subscribed(query.bot, query.from_user.id):
        await safe_answer(query, "❌ Ты ещё не подписан!", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()

    if user:
        await safe_render(query, f"🏁 С возвращением, <b>{user.username}</b>!", get_main_menu(is_owner=query.from_user.id in settings.OWNER_IDS))
        return

    await state.set_state(RegState.waiting_username)
    await safe_render(query, "✅ Подписка подтверждена!\n\nПридумай игровой ник (3–20 символов, латиница):")


@router.message(RegState.waiting_username, F.text.regexp(USERNAME_PATTERN))
async def handle_username(message: Message, state: FSMContext):
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

    await state.clear()
    await message.answer(
        f"✅ <b>@{username}</b>, ты в игре!\n\n💰 {settings.DAILY_MONEY} монет\n🎴 {settings.DAILY_ATTEMPTS} попытки",
        reply_markup=get_main_menu(is_owner=message.from_user.id in settings.OWNER_IDS),
        parse_mode="HTML"
    )


@router.message(RegState.waiting_username)
async def handle_bad_username(message: Message):
    await message.answer("❌ Ник должен быть 3–20 символов, латиница, начинаться с буквы.")


@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery):
    await safe_answer(query)
    await safe_render(
        query,
        "🏁 <b>Главное меню</b>",
        get_main_menu(is_owner=query.from_user.id in settings.OWNER_IDS)
    )
