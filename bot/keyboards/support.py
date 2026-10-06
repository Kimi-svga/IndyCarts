"""Клавиатуры поддержки."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import TICKET_CATEGORIES


class SupportMenu(CallbackData, prefix="sup"):
    action: str
    ticket_id: int = 0
    category: str = ""


def get_support_menu(open_count: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📩 Создать тикет", callback_data=SupportMenu(action="new").pack())
    b.button(
        text=f"📋 Мои тикеты ({open_count})",
        callback_data=SupportMenu(action="my").pack(),
    )
    b.button(text="📖 FAQ", callback_data=SupportMenu(action="faq").pack())
    b.button(text="🔙 Назад", callback_data="menu:back")
    b.adjust(1)
    return b.as_markup()


def get_categories_menu() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, name in TICKET_CATEGORIES.items():
        b.button(
            text=name,
            callback_data=SupportMenu(action="cat", category=code).pack(),
        )
    b.button(text="🔙 Назад", callback_data=SupportMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_ticket_actions(ticket_id: int, is_owner: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="✍️ Ответить",
        callback_data=SupportMenu(action="reply", ticket_id=ticket_id).pack(),
    )
    if is_owner:
        b.button(
            text="🔒 Закрыть",
            callback_data=SupportMenu(action="close", ticket_id=ticket_id).pack(),
        )
    b.button(text="🔙 Назад", callback_data=SupportMenu(action="my").pack())
    b.adjust(2, 1)
    return b.as_markup()


def get_staff_ticket_actions(ticket_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="✍️ Ответить",
        callback_data=f"support_panel:reply:{ticket_id}",
    )
    b.button(
        text="✅ Решён",
        callback_data=f"support_panel:resolve:{ticket_id}",
    )
    b.button(
        text="🔒 Закрыть",
        callback_data=f"support_panel:close:{ticket_id}",
    )
    b.button(
        text="🚨 Срочный",
        callback_data=f"support_panel:urgent:{ticket_id}",
    )
    b.button(text="🔙 К списку", callback_data="support_panel:list:open")
    b.adjust(2, 2, 1)
    return b.as_markup()
