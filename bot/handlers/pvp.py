from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings

router = Router()


@router.callback_query(MainMenu.filter(F.action == "pvp"))
async def cb_pvp(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "⚔️ <b>PvP — Дуэли на кубах</b>\n\n"
        "Ставь карты, бросай 2 кубика.\n"
        "У кого больше — забирает всё.\n\n"
        f"💰 Стоимость: {settings.PVP_FEE} монет\n\n"
        "🚧 В разработке...",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
    ) 
