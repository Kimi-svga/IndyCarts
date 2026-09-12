from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


class MainMenu(CallbackData, prefix="menu"):
    action: str


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Профиль", callback_data=MainMenu(action="profile"))
    builder.button(text="🃏 Карты", callback_data=MainMenu(action="cards"))
    builder.button(text="💹 Биржа", callback_data=MainMenu(action="market"))
    builder.button(text="⚔️ PvP", callback_data=MainMenu(action="pvp"))
    builder.button(text="🏦 Банк", callback_data=MainMenu(action="bank"))
    builder.button(text="🏆 Рейтинг", callback_data=MainMenu(action="rating"))
    builder.button(text="🎨 Лимитки", callback_data=MainMenu(action="limited"))
    builder.button(text="📅 Ежедневка", callback_data=MainMenu(action="daily"))
    builder.adjust(2)
    return builder.as_markup()


def get_back_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    return builder.as_markup()
