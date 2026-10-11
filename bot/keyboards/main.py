"""Главное меню Simply Flag — 21 кнопка Пьера в 2 колонки."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MainMenu(CallbackData, prefix="menu"):
    """Главное меню."""
    action: str


def get_main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    """Главное меню Simply Flag — 21 кнопка в 2 колонки."""
    b = InlineKeyboardBuilder()

    b.button(text="🎴 Пит-стоп", callback_data=MainMenu(action="drop").pack())
    b.button(text="🃏 Мой гараж", callback_data=MainMenu(action="cards").pack())

    b.button(text="💰 F1 Store", callback_data=MainMenu(action="shop").pack())
    b.button(text="🎁 Контракты", callback_data=MainMenu(action="tasks").pack())

    b.button(text="🏆 Чемпионат", callback_data=MainMenu(action="rating").pack())
    b.button(text="🔥 Limited Grid", callback_data=MainMenu(action="limited").pack())

    b.button(text="⚔️ Grid Battles", callback_data=MainMenu(action="pvp").pack())
    b.button(text="🎲 Race Dice", callback_data=MainMenu(action="cubes").pack())

    b.button(text="🚗 DRS Zone", callback_data=MainMenu(action="races").pack())
    b.button(text="🏁 Гран-при", callback_data=MainMenu(action="seasons").pack())

    b.button(text="🏰 Конструкторы", callback_data=MainMenu(action="clans").pack())
    b.button(text="🤝 Трансферное окно", callback_data=MainMenu(action="trade").pack())

    b.button(text="🎯 Аукцион паддока", callback_data=MainMenu(action="auction").pack())
    b.button(text="👥 Напарники", callback_data=MainMenu(action="friends").pack())

    b.button(text="🏦 Командный бюджет", callback_data=MainMenu(action="bank").pack())
    b.button(text="🎫 Paddock Pass", callback_data=MainMenu(action="plus").pack())

    b.button(text="🎯 Race Predictions", callback_data=MainMenu(action="predictions").pack())
    b.button(text="🔧 Пит-бокс", callback_data=MainMenu(action="merge").pack())

    b.button(text="🔗 Пригласить в команду", callback_data=MainMenu(action="ref").pack())
    b.button(text="📖 Race Control", callback_data=MainMenu(action="support").pack())

    b.button(text="ℹ️ Simply Flag HQ", callback_data=MainMenu(action="about").pack())

    if is_owner:
        b.button(text="👑 Панель", callback_data=MainMenu(action="admin_panel").pack())

    b.adjust(2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1)

    return b.as_markup()


def get_back_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_cancel_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()
