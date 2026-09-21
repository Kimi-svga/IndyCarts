from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


class MainMenu(CallbackData, prefix="menu"):
    action: str


def get_main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="👤 Профиль", callback_data=MainMenu(action="profile"))
    b.button(text="🃏 Карты", callback_data=MainMenu(action="cards"))
    b.button(text="💹 Биржа", callback_data=MainMenu(action="market"))
    b.button(text="🛒 Магазин", callback_data=MainMenu(action="shop"))
    b.button(text="⚔️ PvP", callback_data=MainMenu(action="pvp"))
    b.button(text="🏦 Банк", callback_data=MainMenu(action="bank"))
    b.button(text="🏆 Рейтинг", callback_data=MainMenu(action="rating"))
    b.button(text="👥 Рефералка", callback_data=MainMenu(action="ref"))
    b.button(text="📅 Ежедневка", callback_data=MainMenu(action="daily"))
    if is_owner:
        b.button(text="👑 Панель", callback_data=MainMenu(action="admin_panel"))
    b.adjust(3, 3, 3, 1)
    return b.as_markup()


def get_back_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    return b.as_markup() 
