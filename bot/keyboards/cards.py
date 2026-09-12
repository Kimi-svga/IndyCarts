from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


class CardsMenu(CallbackData, prefix="cards"):
    action: str


def get_cards_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🃏 Моя коллекция", callback_data=CardsMenu(action="my"))
    builder.button(text="🎴 Дроп", callback_data=CardsMenu(action="drop"))
    builder.button(text="🔙 Назад", callback_data=CardsMenu(action="back"))
    builder.adjust(1)
    return builder.as_markup() 
