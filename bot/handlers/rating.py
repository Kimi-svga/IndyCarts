"""Рейтинги: топ по балансу, сезонный + вечный PvP."""

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu
from bot.utils.stable import safe_answer, safe_render
from db.models import PvpSeason, User
from db.session import AsyncSessionLocal
from services.pvp import get_rank_title

router = Router()


class RatingMenu(CallbackData, prefix="rate"):
    """Меню рейтинга."""
    action: str


@router.callback_query(MainMenu.filter(F.action == "rating"))
async def cb_rating(query: CallbackQuery) -> None:
    await safe_answer(query)

    b = InlineKeyboardBuilder()
    b.button(text="💰 Топ по балансу", callback_data=RatingMenu(action="money").pack())
    b.button(text="⚔️ Топ сезона", callback_data=RatingMenu(action="pvp_season").pack())
    b.button(text="👑 Вечный топ PvP", callback_data=RatingMenu(action="pvp_eternal").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)

    await safe_render(query, "🏆 <b>Рейтинги</b>\n\nВыбери:", b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "menu"))
async def cb_rating_menu(query: CallbackQuery) -> None:
    await safe_answer(query)
    await cb_rating(query)


@router.callback_query(RatingMenu.filter(F.action == "money"))
async def cb_rating_money(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User).order_by(User.balance.desc()).limit(10)
        )).scalars().all()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "💰 <b>Топ-10 по балансу</b>\n\n"
    for i, u in enumerate(users):
        text += f"{medals[i]} @{u.username} — <b>{u.balance:,}</b>\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu").pack())
    b.adjust(1)
    await safe_render(query, text, b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "pvp_season"))
async def cb_rating_pvp_season(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        season = (await session.execute(
            select(PvpSeason).where(PvpSeason.is_active == True)
        )).scalar_one_or_none()

        if season is None:
            await safe_render(query, "❌ Сезон не активен", MainMenu(action="back").pack())
            return

        users = (await session.execute(
            select(User).order_by(User.pvp_rating.desc()).limit(10)
        )).scalars().all()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = f"⚔️ <b>Топ сезона S{season.number}</b>\n\n"
    for i, u in enumerate(users):
        title = get_rank_title(u.pvp_rating)
        text += (
            f"{medals[i]} @{u.username} — <b>{u.pvp_rating}</b>\n"
            f"    {title} · {u.pvp_wins}W / {u.pvp_losses}L\n"
        )

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu").pack())
    b.adjust(1)
    await safe_render(query, text, b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "pvp_eternal"))
async def cb_rating_pvp_eternal(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User).order_by(User.pvp_wins_total.desc()).limit(10)
        )).scalars().all()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "👑 <b>Вечный топ PvP</b>\n\n"
    for i, u in enumerate(users):
        total = u.pvp_wins_total + u.pvp_losses_total
        winrate = (u.pvp_wins_total / total * 100) if total > 0 else 0
        text += (
            f"{medals[i]} @{u.username} — <b>{u.pvp_wins_total}W</b>\n"
            f"    WR: {winrate:.1f}% · {total} боёв\n"
        )

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu").pack())
    b.adjust(1)
    await safe_render(query, text, b.as_markup()) 
