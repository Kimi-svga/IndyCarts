"""Клавиатуры аукциона."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu
from core.constants import AUCTION_DURATIONS


class AuctionMenu(CallbackData, prefix="auc"):
    action: str
    auction_id: int = 0
    index: int = 0
    duration: str = ""


def get_auction_main_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔍 Смотреть лоты", callback_data=AuctionMenu(action="browse").pack())
    b.button(text="➕ Выставить карту", callback_data=AuctionMenu(action="sell_pick").pack())
    b.button(text="📋 Мои лоты", callback_data=AuctionMenu(action="my").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_duration_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, (label, _) in AUCTION_DURATIONS.items():
        b.button(
            text=label,
            callback_data=AuctionMenu(action="dur", duration=code).pack(),
        )
    b.button(text="🔙 Отмена", callback_data=AuctionMenu(action="menu").pack())
    b.adjust(2, 2, 1)
    return b.as_markup()


def get_lot_actions(auction_id: int, index: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="💰 Ставка",
        callback_data=AuctionMenu(action="bid", auction_id=auction_id).pack(),
    )
    b.button(
        text="⚡ Выкупить",
        callback_data=AuctionMenu(action="buyout", auction_id=auction_id).pack(),
    )
    b.button(
        text="🔙 К списку",
        callback_data=AuctionMenu(action="browse").pack(),
    )
    b.adjust(2, 1)
    return b.as_markup()


def get_seller_lot_actions(auction_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🚫 Отменить лот",
        callback_data=AuctionMenu(action="cancel", auction_id=auction_id).pack(),
    )
    b.button(
        text="🔙 К моим лотам",
        callback_data=AuctionMenu(action="my").pack(),
    )
    b.adjust(1)
    return b.as_markup()
