"""Клавиатуры админ-панели."""

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from bot.keyboards.main import MainMenu


class AdminMenu(CallbackData, prefix="admin"):
    action: str


def get_admin_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🃏 Добавить карту", callback_data=AdminMenu(action="add_card"))
    b.button(text="✏️ Редактор карт", callback_data=AdminMenu(action="edit_cards"))
    b.button(text="🎁 Создать промокод", callback_data=AdminMenu(action="add_promo"))
    b.button(text="🏆 Награды топ", callback_data=AdminMenu(action="rewards"))
    b.button(text="📨 Рассылка", callback_data=AdminMenu(action="broadcast"))
    b.button(text="📊 Статистика", callback_data=AdminMenu(action="stats"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()
