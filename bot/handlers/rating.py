"""Рейтинги: топ по балансу, топ по PvP и награды PvP."""

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu
from bot.utils.stable import safe_answer, safe_render
from db.models import Card, PvpReward, User
from db.session import AsyncSessionLocal
from services.pvp import get_rank_title

router = Router()


class RatingMenu(CallbackData, prefix="rate"):
    """Меню рейтинга."""
    action: str


@router.callback_query(MainMenu.filter(F.action == "rating"))
async def cb_rating(query: CallbackQuery) -> None:
    """Показывает меню рейтинга."""
    await safe_answer(query)

    b = InlineKeyboardBuilder()
    b.button(text="💰 Топ по балансу", callback_data=RatingMenu(action="money"))
    b.button(text="⚔️ Топ по PvP", callback_data=RatingMenu(action="pvp"))
    b.button(text="🏆 Награды PvP", callback_data=RatingMenu(action="pvp_rewards"))
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)

    await safe_render(query, "🏆 <b>Рейтинги</b>\n\nВыбери:", b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "menu"))
async def cb_rating_menu(query: CallbackQuery) -> None:
    """Возврат в меню рейтинга."""
    await safe_answer(query)
    await cb_rating(query)


@router.callback_query(RatingMenu.filter(F.action == "money"))
async def cb_rating_money(query: CallbackQuery) -> None:
    """Топ-10 по балансу."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User).order_by(User.balance.desc()).limit(10)
        )).scalars().all()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "💰 <b>Топ-10 по балансу</b>\n\n"
    for i, u in enumerate(users):
        text += f"{medals[i]} @{u.username} — {u.balance}\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "pvp"))
async def cb_rating_pvp(query: CallbackQuery) -> None:
    """Топ-10 по PvP-рейтингу."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        users = (await session.execute(
            select(User).order_by(User.pvp_rating.desc()).limit(10)
        )).scalars().all()

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "⚔️ <b>Топ-10 по PvP</b>\n\n"
    for i, u in enumerate(users):
        title = get_rank_title(u.pvp_rating)
        text += (
            f"{medals[i]} @{u.username} — <b>{u.pvp_rating}</b>\n"
            f"    {title} · {u.pvp_wins}W / {u.pvp_losses}L\n"
        )

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


@router.callback_query(RatingMenu.filter(F.action == "pvp_rewards"))
async def cb_pvp_rewards(query: CallbackQuery) -> None:
    """Показывает награды за топ PvP."""
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        rewards = (await session.execute(
            select(PvpReward).order_by(PvpReward.position)
        )).scalars().all()

        card_ids = [r.reward_card_id for r in rewards if r.reward_card_id]
        cards_map = {}
        if card_ids:
            cards = (await session.execute(
                select(Card).where(Card.id.in_(card_ids))
            )).scalars().all()
            cards_map = {c.id: c.name for c in cards}

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 <b>Награды топ-10 PvP</b>\n\n"

    if not rewards:
        text += "Пока не настроены."
    else:
        for r in rewards:
            emoji = medals[r.position - 1] if 1 <= r.position <= 10 else "•"
            text += f"{emoji} <b>Топ-{r.position}</b>\n"
            if r.reward_money:
                text += f"    💰 {r.reward_money} монет\n"
            if r.reward_attempts:
                text += f"    🎴 {r.reward_attempts} попыток\n"
            if r.reward_card_id:
                card_name = cards_map.get(r.reward_card_id, f"#{r.reward_card_id}")
                text += f"    🎴 <b>{card_name}</b> (кастом)\n"
            text += "\n"

    text += "<i>Выдаются 1-го числа каждого месяца.</i>"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=RatingMenu(action="menu"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup()) 
