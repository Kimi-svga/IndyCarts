"""Реферальная система."""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from db.models import Referral, User
from db.session import AsyncSessionLocal

router = Router()


@router.callback_query(MainMenu.filter(F.action == "ref"))
async def cb_ref(query: CallbackQuery) -> None:
    """Показывает реферальную программу."""
    await safe_answer(query)

    bot_info = await query.bot.get_me()
    bot_username = bot_info.username

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start")
            return

        refs = (await session.execute(
            select(Referral).where(Referral.referrer_id == user.id)
        )).scalars().all()

    link = f"https://t.me/{bot_username}?start=ref_{user.id}"

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей — получай бонусы!\n\n"
        f"<b>Награды:</b>\n"
        f"💰 +{settings.REFERRAL_BONUS_MONEY} монет\n"
        f"🎴 +{settings.REFERRAL_BONUS_ATTEMPTS} попытка\n"
        f"За каждого друга (и тебе, и ему)\n\n"
        f"<b>Твоя ссылка:</b>\n"
        f"<code>{link}</code>\n\n"
        f"👥 Приглашено: <b>{len(refs)}</b>"
    )

    b = InlineKeyboardBuilder()
    b.button(
        text="📤 Поделиться",
        url=f"https://t.me/share/url?url={link}&text=Играй в Indy Carts!",
    )
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup()) 
