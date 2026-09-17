from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from datetime import datetime, timedelta
from bot.keyboards.main import MainMenu, get_back_menu
from core.config import settings
from db.session import AsyncSessionLocal
from db.models import User

router = Router()

@router.callback_query(MainMenu.filter(F.action == "bank"))
async def cb_bank(query: CallbackQuery):
    await query.answer()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == query.from_user.id))).scalar_one_or_none()
        if not user:
            await query.message.edit_text("❌ Сначала /start")
            return
        loan = f"\n⚠️ Долг: <b>{user.loan_amount}</b>" if user.loan_amount > 0 else "\n✅ Нет кредитов"
    await query.message.edit_text(
        f"🏦 <b>P4/9 Bank</b>\n\n💰 Ставка: {int(settings.BANK_RATE*100)}%\n📅 Срок: {settings.BANK_TERM_DAYS} дней\n💵 Макс: {settings.BANK_MAX_LOAN:,}\n{loan}\n\n<code>/loan 5000</code>",
        reply_markup=get_back_menu(), parse_mode="HTML"
    )

@router.message(F.text.startswith("/loan"))
async def cmd_loan(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/loan 5000</code>", parse_mode="HTML")
        return
    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return
    if amount < 100 or amount > settings.BANK_MAX_LOAN:
        await message.answer(f"❌ Сумма от 100 до {settings.BANK_MAX_LOAN}")
        return
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала /start")
            return
        if user.loan_amount > 0:
            await message.answer("❌ Уже есть активный кредит")
            return
        user.balance += amount
        user.loan_amount = int(amount * (1 + settings.BANK_RATE))
        user.loan_due_at = datetime.utcnow() + timedelta(days=settings.BANK_TERM_DAYS)
        await session.commit()
        due = user.loan_due_at.strftime('%d.%m.%Y')
        total = user.loan_amount
    await message.answer(
        f"✅ <b>Кредит выдан!</b>\n\n💰 Получено: {amount}\n📅 Вернуть до: {due}\n💵 К возврату: <b>{total}</b>",
        parse_mode="HTML"
    ) 
