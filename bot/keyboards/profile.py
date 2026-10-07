"""Клавиатура профиля."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu
from bot.keyboards.friends import FriendsMenu


def get_profile_menu(
    friends_count: int = 0,
    incoming: int = 0,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    friends_text = f"👥 Друзья ({friends_count})"
    if incoming > 0:
        friends_text += f" · 📥{incoming}"

    b.button(text="🎴 Мои карты", callback_data=MainMenu(action="cards"))
    b.button(text=friends_text, callback_data=FriendsMenu(action="menu").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup() 
