from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
        if user.loan_amount > 0:
            due = user.loan_due_at.strftime('%d.%m.%Y') if user.loan_due_at else "—"
            days_left = (user.loan_due_at - datetime.utcnow()).days if user.loan_due_at else 0
            warning = ""
            if days_left < 0:
                warning = "\n⚠️ <b>ПРОСРОЧКА!</b> Банк забирает карты."
            elif days_left <= 3:
                warning = f"\n⚠️ <b>Осталось {days_left} дней!</b>"
            loan_info = f"\n💰 Долг: <b>{user.loan_amount}</b>\n📅 Вернуть до: {due}\n⏳ Осталось: {days_left} дней{warning}\n"
            builder = InlineKeyboardBuilder()
            builder.button(text="💸 Досрочно погасить", callback_data="repay_menu")
            builder.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
            builder.adjust(1)
            await query.message.edit_text(
                f"🏦 <b>P4/9 Bank</b>\n\n💰 Ставка: {int(settings.BANK_RATE*100)}%\n📅 Срок: {settings.BANK_TERM_DAYS} дней\n💵 Макс: {settings.BANK_MAX_LOAN:,}\n{loan_info}\n<code>/repay сумма</code> — погасить",
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        else:
            await query.message.edit_text(
                f"🏦 <b>P4/9 Bank</b>\n\n💰 Ставка: {int(settings.BANK_RATE*100)}%\n📅 Срок: {settings.BANK_TERM_DAYS} дней\n💵 Макс: {settings.BANK_MAX_LOAN:,}\n\n✅ Нет активных кредитов\n\n<code>/loan 5000</code> — взять кредит",
                reply_markup=get_back_menu(),
                parse_mode="HTML"
            )


@router.callback_query(F.data == "repay_menu")
async def cb_repay_menu(query: CallbackQuery):
    await query.answer()
    await query.message.edit_text("💸 <b>Досрочное погашение</b>\n\nВведи сумму:\n<code>/repay 5000</code>", reply_markup=get_back_menu(), parse_mode="HTML")


@router.message(F.text.startswith("/repay"))
async def cmd_repay(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/repay 5000</code>", parse_mode="HTML")
        return
    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        if not user or user.loan_amount <= 0:
            await message.answer("❌ Нет активного кредита")
            return
        if user.balance < amount:
            await message.answer("❌ Не хватает монет")
            return
        amount = min(amount, user.loan_amount)
        user.balance -= amount
        user.loan_amount -= amount
        user.trust_score += 1
        if user.loan_amount <= 0:
            user.loan_amount = 0
            user.loan_due_at = None
            text = f"✅ <b>Кредит погашен!</b>\n\nСписано: {amount}\n📈 Доверие: +1"
        else:
            text = f"✅ <b>Досрочное погашение</b>\n\nСписано: {amount}\nОсталось: <b>{user.loan_amount}</b>\n📈 Доверие: +1"
        await session.commit()
    await message.answer(text, parse_mode="HTML")


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
        f"✅ <b>Кредит выдан!</b>\n\n💰 Получено: {amount}\n📅 Вернуть до: {due}\n💵 К возврату: <b>{total}</b>\n\n⚠️ <b>Внимание!</b> Если не выплатишь вовремя:\n1. Банк заберёт твои карты\n2. Баланс уйдёт в минус\n3. PvP будет заблокирован",
        parse_mode="HTML"
        ) 
