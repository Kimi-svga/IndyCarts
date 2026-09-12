from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from db.session import AsyncSessionLocal
from db.models import User

router = Router()


@router.callback_query(MainMenu.filter(F.action == "rating"))
async def cb_rating(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        stmt = select(User).order_by(User.rating_total.desc()).limit(10)
        result = await session.execute(stmt)
        users = result.scalars().all()

    if not users:
        text = "🏆 <b>Рейтинг пуст</b>"
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        text = "🏆 <b>Топ-10 игроков</b>\n\n"
        for i, u in enumerate(users):
            text += f"{medals[i]} @{u.username} — {u.rating_total}\n"

    await query.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="HTML") 
