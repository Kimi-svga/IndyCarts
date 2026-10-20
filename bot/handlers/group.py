"""Group Integration — игра и профиль прямо в чатах."""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import desc, select

from db.models import User
from db.session import AsyncSessionLocal
from bot.utils.stable import safe_answer

router = Router()

# ==========================================
# /start в группе
# ==========================================
@router.message(CommandStart(), F.chat.type.in_({"group", "supergroup"}))
async def cmd_start_group(message: Message) -> None:
    bot_info = await message.bot.get_me()
    
    b = InlineKeyboardBuilder()
    b.button(
        text="👤 Мой профиль", 
        callback_data=f"grp_profile_{message.from_user.id}"
    )
    b.adjust(1)

    await message.answer(
        f"🏁 <b>IndyCarts в чате!</b>\n\n"
        f"Привет, {message.from_user.first_name}!\n"
        f"Теперь вы можете играть прямо здесь.\n\n"
        f"Доступные команды:\n"
        f"👤 /me — Показать профиль\n"
        f"🏆 /top — Топ игроков\n"
        f"⚔️ /duel — Вызвать на PvP (ответом на сообщение)",
        reply_markup=b.as_markup(),
        parse_mode="HTML"
    )

# ==========================================
# /me — Профиль в группе (видят все, жмет только владелец)
# ==========================================
@router.message(Command("me"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_me_group(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

    if not user:
        await message.answer("❌ Ты не зарегистрирован. Напиши боту в личку и нажми /start.")
        return

    # Формируем красивый профиль
    text = (
        f"👤 <b>Профиль @{user.username}</b>\n"
        f"──────────────────\n"
        f"💰 Баланс: <b>{user.balance:,}</b>\n"
        f"⚔️ PvP Рейтинг: <b>{user.pvp_rating}</b> ({user.pvp_wins}W/{user.pvp_losses}L)\n"
        f"🔥 Стрик: <b>{user.daily_streak}</b>\n"
        f"🎴 Попытки: <b>{user.daily_attempts}</b>\n"
        f"💎 Indy+: {'✅ Активен' if user.plus_tier == 'indy_plus' else '❌ Нет'}"
    )

    # Кнопки управления (зашиваем ID владельца)
    b = InlineKeyboardBuilder()
    b.button(text="🎴 Мои карты", callback_data=f"grp_cards_{user.telegram_id}")
    b.button(text="💰 Баланс", callback_data=f"grp_balance_{user.telegram_id}")
    b.adjust(2)

    await message.answer(text, reply_markup=b.as_markup(), parse_mode="HTML")

# ==========================================
# Обработка кнопок профиля (ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА)
# ==========================================
@router.callback_query(F.data.startswith("grp_"))
async def handle_group_actions(query: CallbackQuery) -> None:
    parts = query.data.split("_")
    action = parts[1]
    owner_id = int(parts[2])

    # --- ЗАЩИТА ОТ ЧУЖИХ НАЖАТИЙ ---
    if query.from_user.id != owner_id:
        await safe_answer(
            query, 
            "⛔ Это чужой профиль. Ты не можешь управлять им.", 
            show_alert=True
        )
        return

    # Если нажал владелец:
    if action == "cards":
        await safe_answer(query, "У тебя 42 карты в коллекции (демо)", show_alert=True)
        # Тут в будущем можно выводить список карт
        
    elif action == "balance":
        async with AsyncSessionLocal() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == query.from_user.id)
            )).scalar_one_or_none()
            if user:
                await safe_answer(query, f"💰 Твой баланс: {user.balance:,} монет", show_alert=True)

    elif action == "profile":
        # Кнопка "Мой профиль" из /start
        await safe_answer(query, "Открой /me, чтобы увидеть профиль", show_alert=True)

# ==========================================
# /top — Топ игроков
# ==========================================
@router.message(Command("top"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_top_group(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        top_users = (await session.execute(
            select(User).order_by(desc(User.pvp_rating)).limit(5)
        )).scalars().all()

    if not top_users:
        await message.answer("В игре пока нет игроков.")
        return

    text = "🏆 <b>Топ-5 игроков по PvP:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, u in enumerate(top_users):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        text += f"{medal} @{u.username} — <b>{u.pvp_rating}</b> ELO\n"

    await message.answer(text, parse_mode="HTML")
