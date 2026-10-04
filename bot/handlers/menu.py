"""Главное меню — единая точка входа и возврата (патч 0.7.0)."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_main_menu
from bot.utils.main_menu import build_main_menu_text
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from db.models import User
from db.session import AsyncSessionLocal

router = Router()


async def show_main_menu(
    target: Message | CallbackQuery,
    user: User | None = None,
) -> None:
    """Показывает главное меню."""
    async with AsyncSessionLocal() as session:
        if user is None:
            telegram_id = getattr(target.from_user, "id", None)
            if telegram_id is None:
                return

            user = (await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )).scalar_one_or_none()

        if user is None:
            if isinstance(target, CallbackQuery):
                await safe_answer(target, "❌ Сначала /start", show_alert=True)
            else:
                await target.answer("❌ Сначала /start")
            return

        text = await build_main_menu_text(user, session)
        is_owner = user.telegram_id in settings.OWNER_IDS
        markup = get_main_menu(is_owner=is_owner)

    if isinstance(target, CallbackQuery):
        await safe_render(target, text, markup)
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(MainMenu.filter(F.action == "back"))
async def cb_back(query: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await safe_answer(query)
    await show_main_menu(query) 
