"""Клавиатуры редактора карт (всё кнопками)."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu


class ACard(CallbackData, prefix="acd"):
    action: str
    card_id: int = 0
    index: int = 0
    value: str = ""


def get_card_editor(card_id: int, in_drop: bool = True) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📝 Название", callback_data=ACard(action="edit_name", card_id=card_id).pack())
    b.button(text="🖼 Картинка", callback_data=ACard(action="edit_image", card_id=card_id).pack())
    b.button(text="🎨 Редкость", callback_data=ACard(action="edit_rarity", card_id=card_id).pack())
    b.button(text="🏁 Команда", callback_data=ACard(action="edit_team", card_id=card_id).pack())
    b.button(text="📅 Год", callback_data=ACard(action="edit_year", card_id=card_id).pack())
    b.button(text="💰 Цена", callback_data=ACard(action="edit_price", card_id=card_id).pack())
    b.button(text="⚖️ Вес дропа", callback_data=ACard(action="edit_weight", card_id=card_id).pack())
    b.button(text="📜 Тираж", callback_data=ACard(action="edit_supply", card_id=card_id).pack())
    b.button(text="📁 Коллекция", callback_data=ACard(action="edit_collection", card_id=card_id).pack())
    drop_text = "🔄 Убрать из дропа" if in_drop else "▶️ Вернуть в дроп"
    b.button(text=drop_text, callback_data=ACard(action="toggle_drop", card_id=card_id).pack())
    b.button(text="❌ Удалить карту", callback_data=ACard(action="delete", card_id=card_id).pack())
    b.button(text="🔙 К списку", callback_data=ACard(action="list", index=0).pack())
    b.adjust(2, 2, 2, 2, 1, 1, 1)
    return b.as_markup()


def get_rarity_menu(card_id: int) -> InlineKeyboardMarkup:
    from core.constants import RARITIES, RARITY_EMOJI, RARITY_NAMES
    b = InlineKeyboardBuilder()
    for r in RARITIES:
        b.button(
            text=f"{RARITY_EMOJI[r]} {RARITY_NAMES[r]}",
            callback_data=ACard(action="set_rarity", card_id=card_id, value=r).pack(),
        )
    b.button(text="🔙 Назад", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(2, 2, 2, 1, 1)
    return b.as_markup()


def get_team_menu(card_id: int, teams: list[str], index: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    per_page = 8
    start = index * per_page
    end = start + per_page
    page_teams = teams[start:end]

    for t in page_teams:
        b.button(
            text=t[:30],
            callback_data=ACard(action="set_team", card_id=card_id, value=t).pack(),
        )

    if index > 0:
        b.button(text="⬅️", callback_data=ACard(action="team_page", card_id=card_id, index=index - 1).pack())
    if end < len(teams):
        b.button(text="➡️", callback_data=ACard(action="team_page", card_id=card_id, index=index + 1).pack())

    b.button(text="✏️ Своя", callback_data=ACard(action="set_team_manual", card_id=card_id).pack())
    b.button(text="🔙 Назад", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(2, 2, 2, 2, 2, 1, 1)
    return b.as_markup()


def get_year_menu(card_id: int, years: list[int], index: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    per_page = 8
    start = index * per_page
    end = start + per_page
    page_years = years[start:end]

    for y in page_years:
        b.button(
            text=str(y),
            callback_data=ACard(action="set_year", card_id=card_id, value=str(y)).pack(),
        )

    if index > 0:
        b.button(text="⬅️", callback_data=ACard(action="year_page", card_id=card_id, index=index - 1).pack())
    if end < len(years):
        b.button(text="➡️", callback_data=ACard(action="year_page", card_id=card_id, index=index + 1).pack())

    b.button(text="✏️ Свой", callback_data=ACard(action="set_year_manual", card_id=card_id).pack())
    b.button(text="🔙 Назад", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(4, 4, 2, 1, 1)
    return b.as_markup()


def get_price_menu(card_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="-1000", callback_data=ACard(action="price_delta", card_id=card_id, value="-1000").pack())
    b.button(text="-100", callback_data=ACard(action="price_delta", card_id=card_id, value="-100").pack())
    b.button(text="-10", callback_data=ACard(action="price_delta", card_id=card_id, value="-10").pack())
    b.button(text="+10", callback_data=ACard(action="price_delta", card_id=card_id, value="10").pack())
    b.button(text="+100", callback_data=ACard(action="price_delta", card_id=card_id, value="100").pack())
    b.button(text="+1000", callback_data=ACard(action="price_delta", card_id=card_id, value="1000").pack())
    b.button(text="✏️ Ввести вручную", callback_data=ACard(action="set_price_manual", card_id=card_id).pack())
    b.button(text="🔙 Назад", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(3, 3, 1, 1)
    return b.as_markup()


def get_collection_menu(card_id: int, collections: list, index: int = 0) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    per_page = 8
    start = index * per_page
    end = start + per_page
    page_col = collections[start:end]

    for col in page_col:
        emoji = col.emoji or "📁"
        b.button(
            text=f"{emoji} {col.name[:25]}",
            callback_data=ACard(action="set_collection", card_id=card_id, value=str(col.id)).pack(),
        )

    if index > 0:
        b.button(text="⬅️", callback_data=ACard(action="col_page", card_id=card_id, index=index - 1).pack())
    if end < len(collections):
        b.button(text="➡️", callback_data=ACard(action="col_page", card_id=card_id, index=index + 1).pack())

    b.button(text="➕ Создать", callback_data=ACard(action="create_collection", card_id=card_id).pack())
    b.button(text="❌ Без коллекции", callback_data=ACard(action="set_collection", card_id=card_id, value="0").pack())
    b.button(text="🔙 Назад", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(2, 2, 2, 2, 1, 1, 1)
    return b.as_markup()


def get_delete_confirm(card_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Да, удалить", callback_data=ACard(action="delete_confirm", card_id=card_id).pack())
    b.button(text="🔙 Отмена", callback_data=ACard(action="view", card_id=card_id).pack())
    b.adjust(2)
    return b.as_markup()


def get_card_list_nav(index: int, total_pages: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=ACard(action="list", index=index - 1).pack())
    b.button(text=f"{index + 1}/{total_pages}", callback_data="noop")
    if index < total_pages - 1:
        b.button(text="➡️", callback_data=ACard(action="list", index=index + 1).pack())
    b.button(text="🔍 Поиск", callback_data=ACard(action="search").pack())
    b.button(text="🔙 В админку", callback_data=MainMenu(action="admin_panel"))
    b.adjust(3, 1, 1)
    return b.as_markup()
