"""Клавиатуры карт: меню, фильтр, слияние, чеклист."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu


# ═════════════════════════════════════════════
# CALLBACK DATA
# ═════════════════════════════════════════════

class CardsMenu(CallbackData, prefix="cards"):
    """Меню карт."""
    action: str


class CardsFilter(CallbackData, prefix="cflt"):
    """Фильтр по редкости (для «Моей коллекции»)."""
    rarity: str


class FullCollectionCD(CallbackData, prefix="fcol"):
    """Пагинация и фильтр полной коллекции (чеклист)."""
    action: str          # "filter" | "page"
    rarity: str = "all"
    page: int = 0


# ═════════════════════════════════════════════
# МЕНЮ КАРТ
# ═════════════════════════════════════════════

def get_cards_menu() -> InlineKeyboardMarkup:
    """Меню карт: коллекция, все карты, дроп, слияние, топ редких."""
    b = InlineKeyboardBuilder()
    b.button(text="🃏 Моя коллекция", callback_data=CardsMenu(action="my"))
    b.button(text="📚 Все карты", callback_data=CardsMenu(action="full"))
    b.button(text="🎴 Дроп", callback_data=CardsMenu(action="drop"))
    b.button(text="🏆 Топ редких", callback_data=CardsMenu(action="rarest"))
    b.button(text="🔀 Слияние", callback_data=CardsMenu(action="merge"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ФИЛЬТР «МОЕЙ КОЛЛЕКЦИИ»
# ═════════════════════════════════════════════

def get_filter_menu() -> InlineKeyboardMarkup:
    """Фильтр коллекции по редкости."""
    b = InlineKeyboardBuilder()
    b.button(text="🔵 Basic", callback_data=CardsFilter(rarity="basic"))
    b.button(text="🟢 Rare", callback_data=CardsFilter(rarity="rare"))
    b.button(text="🟣 Epic", callback_data=CardsFilter(rarity="epic"))
    b.button(text="🟠 Mythic", callback_data=CardsFilter(rarity="mythic"))
    b.button(text="🟡 Legendary", callback_data=CardsFilter(rarity="legendary"))
    b.button(text="🔴 Limited", callback_data=CardsFilter(rarity="limited"))
    b.button(text="⭐ Season", callback_data=CardsFilter(rarity="season"))
    b.button(text="📊 Все", callback_data=CardsFilter(rarity="all"))
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back_to_cards"))
    b.adjust(3, 3, 2, 1)
    return b.as_markup()


# ═════════════════════════════════════════════
# СЛИЯНИЕ
# ═════════════════════════════════════════════

def get_merge_menu() -> InlineKeyboardMarkup:
    """Меню слияния."""
    b = InlineKeyboardBuilder()
    b.button(text="🔵 Basic ×3 → Rare", callback_data="mg_basic")
    b.button(text="🟢 Rare ×3 → Epic", callback_data="mg_rare")
    b.button(text="🟣 Epic ×3 → Mythic", callback_data="mg_epic")
    b.button(text="🟠 Mythic ×3 → Legendary", callback_data="mg_mythic")
    b.button(text="🟡 Legendary ×3 → Limited (20%)", callback_data="mg_legendary")
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back_to_cards"))
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ЧЕКЛИСТ «ВСЕ КАРТЫ»
# ═════════════════════════════════════════════

def get_full_collection_menu(
    rarity: str,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Чеклист всех карт: фильтр по редкости + пагинация."""
    b = InlineKeyboardBuilder()

    # Фильтр по редкости (без эмодзи)
    rarities = [
        ("all", "Все"),
        ("basic", "Basic"),
        ("rare", "Rare"),
        ("epic", "Epic"),
        ("mythic", "Mythic"),
        ("legendary", "Legendary"),
        ("limited", "Limited"),
        ("season", "Season"),
    ]
    for code, label in rarities:
        active = "✅ " if code == rarity else ""
        b.button(
            text=f"{active}{label}",
            callback_data=FullCollectionCD(action="filter", rarity=code).pack(),
        )
    b.adjust(4, 4)

    # Пагинация
    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(
            text="⬅️",
            callback_data=FullCollectionCD(
                action="page", rarity=rarity, page=page - 1,
            ).pack(),
        )
    nav.button(text=f"{page + 1}/{total_pages}", callback_data="noop")
    if page < total_pages - 1:
        nav.button(
            text="➡️",
            callback_data=FullCollectionCD(
                action="page", rarity=rarity, page=page + 1,
            ).pack(),
        )
    nav.adjust(3)
    b.attach(nav)

    # Назад
    b.button(text="🔙 Назад", callback_data=CardsMenu(action="back_to_cards"))
    b.adjust(1)

    return b.as_markup() 
