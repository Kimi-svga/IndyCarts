"""Меню Экономики — Simply Flag."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.main import EconomyMenu, MainMenu, get_economy_menu
from bot.utils.stable import safe_answer, safe_render

router = Router()


@router.callback_query(MainMenu.filter(F.action == "economy_menu"))
async def cb_economy_menu(query: CallbackQuery) -> None:
    """Главный экран раздела Экономика."""
    await safe_answer(query)

    text = (
        "💰 <b>ЭКОНОМИКА</b>\n\n"
        "Магазин, бюджет, аукцион, обмен.\n\n"
        "Выбери раздел:"
    )

    await safe_render(query, text, get_economy_menu())


@router.callback_query(EconomyMenu.filter(F.action == "back"))
async def cb_economy_back(query: CallbackQuery) -> None:
    """Возврат в меню Экономики."""
    await safe_answer(query)
    await cb_economy_menu(query)


# ═════════════════════════════════════════════
# РОУТЫ НА СУЩЕСТВУЮЩИЕ ФИЧИ
# ═════════════════════════════════════════════

@router.callback_query(EconomyMenu.filter(F.action == "shop"))
async def cb_shop(query: CallbackQuery) -> None:
    """F1 Store → Shop."""
    await safe_answer(query)
    from bot.handlers.shop import cb_shop as cb_sh
    await cb_sh(query)


@router.callback_query(EconomyMenu.filter(F.action == "bank"))
async def cb_bank(query: CallbackQuery) -> None:
    """Командный бюджет → Bank."""
    await safe_answer(query)
    from bot.handlers.bank import cb_bank as cb_bk
    await cb_bk(query)


@router.callback_query(EconomyMenu.filter(F.action == "auction"))
async def cb_auction(query: CallbackQuery) -> None:
    """Аукцион паддока → Auction."""
    await safe_answer(query)
    from bot.handlers.auction import cb_auction as cb_ac
    await cb_ac(query)


@router.callback_query(EconomyMenu.filter(F.action == "trade"))
async def cb_trade(query: CallbackQuery) -> None:
    """Трансферное окно → Trade (обмен)."""
    await safe_answer(query)

    # Открываем меню обмена — через профиль или друзей
    from bot.handlers.trade import cb_trade_start
    # Пока заглушка — переход в друзей (там трейд)
    from bot.handlers.friends import cb_menu as cb_fr
    await cb_fr(query)


@router.callback_query(EconomyMenu.filter(F.action == "merge"))
async def cb_merge(query: CallbackQuery) -> None:
    """Пит-бокс → Слияние карт."""
    await safe_answer(query)
    from bot.handlers.cards import cb_merge_menu
    await cb_merge_menu(query)
