"""Главное меню и универсальные клавиатуры."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import MAIN_MENU_BUTTONS


class MainMenu(CallbackData, prefix="menu"):
    """Главное меню."""
    action: str


def get_main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    """
    Главное меню — только кнопки.

    Текст инфо-панели рендерится отдельно
    через bot.utils.main_menu.build_main_menu_text().
    """
    b = InlineKeyboardBuilder()

    for label, action in MAIN_MENU_BUTTONS:
        b.button(text=label, callback_data=MainMenu(action=action))

    if is_owner:
        b.button(text="👑 Панель", callback_data=MainMenu(action="admin_panel"))
        b.adjust(3, 3, 3, 1)
    else:
        b.adjust(3, 3, 3)

    return b.as_markup()


def get_back_menu() -> InlineKeyboardMarkup:
    """Кнопка «Назад» → главное меню."""
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_cancel_menu() -> InlineKeyboardMarkup:
    """Кнопка «Отмена» → главное меню."""
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup() 
