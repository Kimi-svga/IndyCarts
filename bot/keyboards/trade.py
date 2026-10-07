"""Клавиатуры обмена картами."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.friends import FriendsMenu


class TradeMenu(CallbackData, prefix="trd"):
    action: str
    trade_id: int = 0
    user_id: int = 0
    index: int = 0
    side: str = ""
    uc_id: int = 0


def get_trade_start_menu(target_id: int, offer_count: int = 0, request_count: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text=f"🎴 Мои карты ({offer_count})",
        callback_data=TradeMenu(action="pick_offer", user_id=target_id).pack(),
    )
    b.button(
        text=f"🃏 Его карты ({request_count})",
        callback_data=TradeMenu(action="pick_request", user_id=target_id).pack(),
    )
    b.button(
        text="💰 Деньги",
        callback_data=TradeMenu(action="money", user_id=target_id).pack(),
    )
    b.button(
        text="✅ Отправить",
        callback_data=TradeMenu(action="send", user_id=target_id).pack(),
    )
    b.button(
        text="🔙 Отмена",
        callback_data=FriendsMenu(action="menu").pack(),
    )
    b.adjust(1)
    return b.as_markup()


def get_trade_offer_actions(trade_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="✅ Принять",
        callback_data=TradeMenu(action="accept", trade_id=trade_id).pack(),
    )
    b.button(
        text="❌ Отклонить",
        callback_data=TradeMenu(action="decline", trade_id=trade_id).pack(),
    )
    b.adjust(2)
    return b.as_markup()


def get_trade_cancel(trade_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🚫 Отменить",
        callback_data=TradeMenu(action="cancel", trade_id=trade_id).pack(),
    )
    b.adjust(1)
    return b.as_markup() 
