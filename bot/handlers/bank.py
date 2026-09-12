from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings

router = Router()


@router.callback_query(MainMenu.filter(F.action == "bank"))
async def cb_bank(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🏦 <b>P4/9 Bank</b>\n\n"
        f"💰 Ставка: {int(settings.BANK_RATE * 100)}%\n"
        f"📅 Срок: {settings.BANK_TERM_DAYS} дней\n"
        f"💵 Максимум: {settings.BANK_MAX_LOAN:,}\n\n"
        "🚧 В разработке...",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
    )
