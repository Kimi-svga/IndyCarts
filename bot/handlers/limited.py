from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.keyboards.main import MainMenu, get_back_menu

router = Router()


@router.callback_query(MainMenu.filter(F.action == "limited"))
async def cb_limited(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text(
        "🎨 <b>Лимитки</b>\n\n"
        "Шлемы, машины, подиумы.\n\n"
        "🚧 В разработке...",
        reply_markup=get_back_menu(),
        parse_mode="HTML"
    )
