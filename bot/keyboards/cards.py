from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

class CardsMenu(CallbackData, prefix="cards"):
    action: str

def get_cards_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🃏 Моя коллекция", callback_data=CardsMenu(action="my"))
    b.button(text="🎴 Дроп", callback_data=CardsMenu(action="drop"))
    b.button(text="🔀 Слияние", callback_data=CardsMenu(action="merge"))
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back"))
    b.adjust(1)
    return b.as_markup()

def get_merge_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔵 Basic ×3 → Rare", callback_data="merge_basic")
    b.button(text="🟢 Rare ×3 → Epic", callback_data="merge_rare")
    b.button(text="🟣 Epic ×3 → Mythic", callback_data="merge_epic")
    b.button(text="🟠 Mythic ×3 → Legendary", callback_data="merge_mythic")
    b.button(text="🟡 Legendary ×3 → Limited (20%)", callback_data="merge_legendary")
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back"))
    b.adjust(1)
    return b.as_markup() 
