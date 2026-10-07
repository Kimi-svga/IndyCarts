"""Клавиатуры раздела друзей."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu


class FriendsMenu(CallbackData, prefix="frn"):
    action: str
    user_id: int = 0
    request_id: int = 0


def get_friends_menu(
    friends_count: int = 0,
    incoming_count: int = 0,
    outgoing_count: int = 0,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➕ Добавить друга", callback_data=FriendsMenu(action="search").pack())
    if incoming_count > 0:
        b.button(
            text=f"📥 Заявки ({incoming_count})",
            callback_data=FriendsMenu(action="incoming").pack(),
        )
    b.button(
        text=f"👥 Мои друзья ({friends_count})",
        callback_data=FriendsMenu(action="list").pack(),
    )
    if outgoing_count > 0:
        b.button(
            text=f"📤 Исходящие ({outgoing_count})",
            callback_data=FriendsMenu(action="outgoing").pack(),
        )
    b.button(text="🔙 Назад", callback_data=MainMenu(action="profile"))
    b.adjust(1)
    return b.as_markup()


def get_back_to_friends() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 К друзьям", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_request_actions(request_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Принять", callback_data=FriendsMenu(action="accept", request_id=request_id).pack())
    b.button(text="❌ Отклонить", callback_data=FriendsMenu(action="reject", request_id=request_id).pack())
    b.button(text="🔙 К друзьям", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(2, 1)
    return b.as_markup()


def get_friend_actions(user_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⚔️ Вызвать на PvP", callback_data=FriendsMenu(action="duel", user_id=user_id).pack())
    b.button(text="❌ Удалить", callback_data=FriendsMenu(action="remove", user_id=user_id).pack())
    b.button(text="🔙 К друзьям", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_user_actions(user_id: int, is_friend: bool = False, request_sent: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if is_friend:
        b.button(text="⚔️ Вызвать на PvP", callback_data=FriendsMenu(action="duel", user_id=user_id).pack())
        b.button(text="✅ Уже в друзьях", callback_data="noop")
    elif request_sent:
        b.button(text="⏳ Заявка отправлена", callback_data="noop")
    else:
        b.button(text="➕ Добавить в друзья", callback_data=FriendsMenu(action="add", user_id=user_id).pack())
    b.button(text="🔙 К друзьям", callback_data=FriendsMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()
