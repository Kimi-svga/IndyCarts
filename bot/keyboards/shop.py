"""Клавиатура магазина попыток."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu


class ShopMenu(CallbackData, prefix="shop"):
    """Меню магазина."""
    action: str
    amount: int = 0


def get_shop_menu() -> InlineKeyboardMarkup:
    """Пакеты попыток."""
    b = InlineKeyboardBuilder()
    b.button(text="🎴 2 попытки — 100 монет", callback_data=ShopMenu(action="buy", amount=2))
    b.button(text="🎴 5 попыток — 250 монет", callback_data=ShopMenu(action="buy", amount=5))
    b.button(text="🎴 10 попыток — 500 монет", callback_data=ShopMenu(action="buy", amount=10))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()
