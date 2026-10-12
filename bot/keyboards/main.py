"""Главное меню и универсальные клавиатуры — Simply Flag."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import MAIN_MENU_BUTTONS


class MainMenu(CallbackData, prefix="menu"):
    """Главное меню."""
    action: str


def get_main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    """
    Главное меню — 8 кнопок + панель для владельца.

    Текст инфо-панели рендерится отдельно
    через bot.utils.main_menu.build_main_menu_text().
    """
    b = InlineKeyboardBuilder()

    for label, action in MAIN_MENU_BUTTONS:
        b.button(text=label, callback_data=MainMenu(action=action))

    # Владелец — панель
    if is_owner:
        b.button(text="👑 Панель", callback_data=MainMenu(action="admin_panel"))

    # Раскладка: 2 колонки
    b.adjust(2, 2, 2, 2, 1)

    return b.as_markup()


def get_back_menu() -> InlineKeyboardMarkup:
    """Кнопка «Назад» → главное меню."""
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_cancel_menu() -> InlineKeyboardMarkup:
    """Кнопка «Отмена» → главное меню."""
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ПОДМЕНЮ — 5 РАЗДЕЛОВ
# ═════════════════════════════════════════════

class RacesMenu(CallbackData, prefix="races"):
    """Меню Гонок."""
    action: str


class EconomyMenu(CallbackData, prefix="econ"):
    """Меню Экономики."""
    action: str


class TasksMenu(CallbackData, prefix="tasks"):
    """Меню Заданий."""
    action: str


class TeamMenu(CallbackData, prefix="team"):
    """Меню Команды."""
    action: str


class InfoMenu(CallbackData, prefix="info"):
    """Меню Информации."""
    action: str


def get_races_menu() -> InlineKeyboardMarkup:
    """Меню Гонок."""
    b = InlineKeyboardBuilder()
    b.button(text="🏆 Чемпионат", callback_data=RacesMenu(action="championship"))
    b.button(text="⚔️ Grid Battles", callback_data=RacesMenu(action="battles"))
    b.button(text="🎲 Race Dice", callback_data=RacesMenu(action="dice"))
    b.button(text="🚗 DRS Zone", callback_data=RacesMenu(action="drs"))
    b.button(text="🏁 Гран-при", callback_data=RacesMenu(action="seasons"))
    b.button(text="🔥 Limited Grid", callback_data=RacesMenu(action="limited"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(2, 2, 2, 1)
    return b.as_markup()


def get_economy_menu() -> InlineKeyboardMarkup:
    """Меню Экономики."""
    b = InlineKeyboardBuilder()
    b.button(text="💰 F1 Store", callback_data=EconomyMenu(action="shop"))
    b.button(text="🏦 Командный бюджет", callback_data=EconomyMenu(action="bank"))
    b.button(text="🎯 Аукцион паддока", callback_data=EconomyMenu(action="auction"))
    b.button(text="🤝 Трансферное окно", callback_data=EconomyMenu(action="trade"))
    b.button(text="🔧 Пит-бокс", callback_data=EconomyMenu(action="merge"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


def get_tasks_menu() -> InlineKeyboardMarkup:
    """Меню Заданий."""
    b = InlineKeyboardBuilder()
    b.button(text="🎁 Контракты", callback_data=TasksMenu(action="tasks"))
    b.button(text="🎫 Paddock Pass", callback_data=TasksMenu(action="plus"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_team_menu() -> InlineKeyboardMarkup:
    """Меню Команды."""
    b = InlineKeyboardBuilder()
    b.button(text="🏰 Конструкторы", callback_data=TeamMenu(action="clans"))
    b.button(text="👥 Напарники", callback_data=TeamMenu(action="friends"))
    b.button(text="🔗 Пригласить в команду", callback_data=TeamMenu(action="ref"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


def get_info_menu() -> InlineKeyboardMarkup:
    """Меню Информации."""
    b = InlineKeyboardBuilder()
    b.button(text="🎯 Race Predictions", callback_data=InfoMenu(action="predictions"))
    b.button(text="📖 Race Control", callback_data=InfoMenu(action="help"))
    b.button(text="ℹ️ Simply Flag HQ", callback_data=InfoMenu(action="about"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup() 
