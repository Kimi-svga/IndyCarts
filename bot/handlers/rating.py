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
        users = (await session.execute(select(User).order_by(User.balance.desc()).limit(10))).scalars().all()
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 <b>Топ-10 по балансу</b>\n\n"
    for i, u in enumerate(users):
        text += f"{medals[i]} @{u.username} — {u.balance}\n"
    await query.message.edit_text(text, reply_markup=get_back_menu(), parse_mode="HTML") 
