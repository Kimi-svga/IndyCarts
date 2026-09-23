"""Старт, регистрация, подписка, реферальная система."""

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_main_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.constants import RESERVED_USERNAMES, USERNAME_PATTERN
from core.logger import setup_logger
from db.models import Referral, User
from db.session import AsyncSessionLocal

router = Router()
logger = setup_logger()
CHANNEL_ID = "@IndyCarts"


class RegState(StatesGroup):
    """Состояние регистрации."""
    waiting_username = State()


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    """Проверяет подписку на канал."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def subscribe_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подписки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/IndyCarts")],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
    ])


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject, state: FSMContext) -> None:
    """
    Обработка /start с реферальной ссылкой.

    Aiogram 3 передаёт параметр через command.args [citation:1][citation:2].
    """
    payload = command.args
    logger.info(f"Deep link payload: {payload}")

    referrer_id = None
    if payload:
        try:
            # Пробуем распарсить как int (ссылка вида ref_123)
            if payload.startswith("ref_"):
                referrer_id = int(payload.replace("ref_", ""))
            else:
                # Пробуем напрямую
                referrer_id = int(payload)
            logger.info(f"Referrer ID: {referrer_id}")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Не удалось распарсить payload: {e}")
            referrer_id = None

    await _start_logic(message, state, referrer_id)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработка /start без реферальной ссылки."""
    await _start_logic(message, state, None)


async def _start_logic(message: Message, state: FSMContext, referrer_id: int | None) -> None:
    """Общая логика /start."""
    if not await is_subscribed(message.bot, message.from_user.id):
        await message.answer(
            "🏁 <b>Добро пожаловать в Indy Carts!</b>\n\n"
            "Чтобы начать, подпишись на канал:\n📢 @IndyCarts\n\n"
            "Потом нажми «✅ Я подписался»",
            reply_markup=subscribe_keyboard(),
            parse_mode="HTML",
        )
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

    if user is not None:
        await message.answer(
            f"🏁 С возвращением, <b>{user.username}</b>!\n\n"
            f"💰 Баланс: {user.balance}\n"
            f"🎴 Попытки: {user.daily_attempts}",
            reply_markup=get_main_menu(is_owner=message.from_user.id in settings.OWNER_IDS),
            parse_mode="HTML",
        )
        return

    await state.update_data(referrer_id=referrer_id)
    await state.set_state(RegState.waiting_username)
    await message.answer(
        "🏁 <b>Добро пожаловать!</b>\n\n"
        "Придумай игровой ник (3–20 символов, латиница):",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(query: CallbackQuery, state: FSMContext) -> None:
    """Проверка подписки."""
    await safe_answer(query)

    if not await is_subscribed(query.bot, query.from_user.id):
        await safe_answer(query, "❌ Ты ещё не подписан!", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

    if user is not None:
        await safe_render(
            query,
            f"🏁 С возвращением, <b>{user.username}</b>!",
            get_main_menu(is_owner=query.from_user.id in settings.OWNER_IDS),
        )
        return

    await state.set_state(RegState.waiting_username)
    await safe_render(
        query,
        "✅ Подписка подтверждена!\n\nПридумай игровой ник (3–20 символов, латиница):",
    )


@router.message(RegState.waiting_username, F.text.regexp(USERNAME_PATTERN))
async def handle_username(message: Message, state: FSMContext) -> None:
    """Регистрация с реферальной наградой."""
    username = message.text.strip()
    norm = username.lower()

    if norm in RESERVED_USERNAMES:
        await message.answer("❌ Ник зарезервирован.")
        return

    data = await state.get_data()
    referrer_id = data.get("referrer_id")

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(
            select(User).where(User.username_normalized == norm)
        )).scalar_one_or_none()

        if existing is not None:
            await message.answer("❌ Ник занят.")
            return

        new_user = User(
            telegram_id=message.from_user.id,
            username=username,
            username_normalized=norm,
            first_name=message.from_user.first_name or "Игрок",
            balance=settings.DAILY_MONEY,
            daily_attempts=settings.DAILY_ATTEMPTS,
            referred_by=referrer_id,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        ref_text = ""
        if referrer_id is not None:
            referrer = (await session.execute(
                select(User).where(User.id == referrer_id)
            )).scalar_one_or_none()

            if referrer is not None and referrer.id != new_user.id:
                already = (await session.execute(
                    select(Referral).where(Referral.referred_id == new_user.id)
                )).scalar_one_or_none()

                if already is None:
                    session.add(Referral(
                        referrer_id=referrer.id,
                        referred_id=new_user.id,
                        rewarded=True,
                    ))
                    referrer.balance += settings.REFERRAL_BONUS_MONEY
                    referrer.daily_attempts += settings.REFERRAL_BONUS_ATTEMPTS
                    referrer.referral_count += 1

                    new_user.balance += settings.REFERRAL_BONUS_MONEY
                    new_user.daily_attempts += settings.REFERRAL_BONUS_ATTEMPTS

                    await session.commit()
                    ref_text = (
                        f"\n\n👥 <b>По приглашению</b>\n"
                        f"💰 +{settings.REFERRAL_BONUS_MONEY} монет\n"
                        f"🎴 +{settings.REFERRAL_BONUS_ATTEMPTS} попытка"
                    )

                    try:
                        await message.bot.send_message(
                            referrer.telegram_id,
                            f"👥 <b>Новый реферал!</b>\n\n"
                            f"@{username} присоединился по твоей ссылке.\n"
                            f"💰 +{settings.REFERRAL_BONUS_MONEY} монет\n"
                            f"🎴 +{settings.REFERRAL_BONUS_ATTEMPTS} попытка",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

    await state.clear()
    await message.answer(
        f"✅ <b>@{username}</b>, ты в игре!\n\n"
        f"💰 {settings.DAILY_MONEY} монет\n"
        f"🎴 {settings.DAILY_ATTEMPTS} попытки{ref_text}",
        reply_markup=get_main_menu(is_owner=message.from_user.id in settings.OWNER_IDS),
        parse_mode="HTML",
    )


@router.message(RegState.waiting_username)
async def handle_bad_username(message: Message) -> None:
    """Неверный формат ника."""
    await message.answer("❌ Ник должен быть 3–20 символов, латиница, начинаться с буквы.")


@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await safe_answer(query)
    await safe_render(
        query,
        "🏁 <b>Главное меню</b>",
        get_main_menu(is_owner=query.from_user.id in settings.OWNER_IDS),
    )
