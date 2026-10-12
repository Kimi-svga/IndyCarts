"""Меню Гонок — Simply Flag."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.main import MainMenu, RacesMenu, get_races_menu
from bot.utils.stable import safe_answer, safe_render

router = Router()


@router.callback_query(MainMenu.filter(F.action == "races_menu"))
async def cb_races_menu(query: CallbackQuery) -> None:
    """Главный экран раздела Гонки."""
    await safe_answer(query)

    text = (
        "🏎 <b>ГОНКИ</b>\n\n"
        "Соревнования, сезоны, battles.\n\n"
        "Выбери раздел:"
    )

    await safe_render(query, text, get_races_menu())


@router.callback_query(RacesMenu.filter(F.action == "back"))
async def cb_races_back(query: CallbackQuery) -> None:
    """Возврат в меню Гонок."""
    await safe_answer(query)
    await cb_races_menu(query)


# ═════════════════════════════════════════════
# РОУТЫ НА СУЩЕСТВУЮЩИЕ ФИЧИ
# ═════════════════════════════════════════════

@router.callback_query(RacesMenu.filter(F.action == "battles"))
async def cb_battles(query: CallbackQuery) -> None:
    """Grid Battles → PvP."""
    await safe_answer(query)
    # Вызываем существующий обработчик PvP
    from bot.handlers.pvp import cb_pvp
    await cb_pvp(query)


@router.callback_query(RacesMenu.filter(F.action == "drs"))
async def cb_drs(query: CallbackQuery) -> None:
    """DRS Zone → Обгоны (пока через PvP, отдельная фича — позже)."""
    await safe_answer(query)
    from bot.handlers.pvp import cb_pvp
    await cb_pvp(query)


@router.callback_query(RacesMenu.filter(F.action == "dice"))
async def cb_dice(query: CallbackQuery) -> None:
    """Race Dice → Кубы (пока заглушка — новая фича позже)."""
    await safe_answer(query)

    text = (
        "🎲 <b>RACE DICE</b>\n\n"
        "Скоро! 🚧\n\n"
        "Кидай кубик, побеждай, забирай банк."
    )

    from bot.keyboards.main import get_back_menu
    from bot.keyboards.main import MainMenu as MM

    # Кнопка возврата в Гонки
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RacesMenu(action="back").pack())
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(RacesMenu.filter(F.action == "championship"))
async def cb_championship(query: CallbackQuery) -> None:
    """Чемпионат → Рейтинг."""
    await safe_answer(query)
    from bot.handlers.rating import cb_rating
    await cb_rating(query)


@router.callback_query(RacesMenu.filter(F.action == "seasons"))
async def cb_seasons(query: CallbackQuery) -> None:
    """Гран-при → PvP Сезоны (пока через PvP)."""
    await safe_answer(query)
    from bot.handlers.pvp import cb_pvp
    await cb_pvp(query)


@router.callback_query(RacesMenu.filter(F.action == "limited"))
async def cb_limited(query: CallbackQuery) -> None:
    """Limited Grid → Limited (лимитки)."""
    await safe_answer(query)
    from bot.handlers.limited import cb_limited as cb_lim
    await cb_lim(query) 
