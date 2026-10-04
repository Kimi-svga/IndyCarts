"""Банк 2.0: кредиты, погашение, рефинансирование, история, FAQ."""

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.keyboards.main import MainMenu, get_back_menu
from bot.utils.stable import safe_answer, safe_render
from core.config import settings
from core.logger import setup_logger
from db.models import Loan, LoanPayment, User
from db.session import AsyncSessionLocal
from services.bank import (
    apply_trust, calculate_max_loan, calculate_total_due,
    can_refinance, early_repay_discount, get_loan_rate,
    get_loan_term, get_trust_rank, is_early_repay,
)

router = Router()
logger = setup_logger()


class BankFaq(CallbackData, prefix="bfaq"):
    """FAQ внутри банка."""
    topic: str


# ─── Меню банка ───

@router.callback_query(MainMenu.filter(F.action == "bank"))
async def cb_bank(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await safe_render(query, "❌ Сначала /start", get_back_menu())
            return

        loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        max_loan = calculate_max_loan(user)
        trust_rank = get_trust_rank(user.trust_score)

    # Нет активного кредита
    if loan is None:
        text = (
            f"🏦 <b>P4/9 Bank</b>\n\n"
            f"💰 Баланс: <b>{user.balance:,}</b>\n"
            f"📊 Доверие: <b>{user.trust_score}</b> · {trust_rank}\n"
            f"🎯 Лимит: <b>{max_loan:,}</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Как взять кредит:</b>\n"
            f"<code>/loan 50000</code>\n\n"
            f"<b>Ставка:</b> 15–30% (от суммы)\n"
            f"<b>Срок:</b> 7–45 дней\n\n"
            f"💡 <i>Чем выше доверие — тем больше лимит.</i>"
        )
        b = InlineKeyboardBuilder()
        b.button(text="❓ Как это работает?", callback_data=BankFaq(topic="menu").pack())
        b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
        b.adjust(1)
        await safe_render(query, text, b.as_markup())
        return

    # Активный кредит
    now = datetime.utcnow()
    days_left = (loan.due_at - now).days
    remaining = loan.total_due - loan.paid

    warning = ""
    if loan.status == "overdue":
        warning = "\n⚠️ <b>ПРОСРОЧКА!</b>"
    elif days_left <= 3:
        warning = f"\n⚠️ <b>Осталось {days_left} дней!</b>"

    text = (
        f"🏦 <b>P4/9 Bank</b>\n\n"
        f"💰 Баланс: <b>{user.balance:,}</b>\n"
        f"📊 Доверие: <b>{user.trust_score}</b> · {trust_rank}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>Активный кредит</b>\n\n"
        f"💵 Взято: <b>{loan.principal:,}</b>\n"
        f"📈 Ставка: <b>{int(loan.rate * 100)}%</b>\n"
        f"💸 К возврату: <b>{loan.total_due:,}</b>\n"
        f"✅ Выплачено: <b>{loan.paid:,}</b>\n"
        f"⏳ Осталось: <b>{remaining:,}</b>\n"
        f"📅 До: <b>{loan.due_at.strftime('%d.%m.%Y')}</b>\n"
        f"⏰ Дней: <b>{days_left}</b>{warning}"
    )

    b = InlineKeyboardBuilder()
    b.button(text="💸 Погасить", callback_data="bank_repay")
    b.button(text="📉 Рефинансировать", callback_data="bank_refinance")
    b.button(text="📜 История", callback_data="bank_history")
    b.button(text="❓ Как это работает?", callback_data=BankFaq(topic="menu").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(2, 1, 1, 1)

    await safe_render(query, text, b.as_markup())


# ─── Взять кредит ───

@router.message(Command("loan"))
async def cmd_loan(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/loan 50000</code>",
            parse_mode="HTML",
        )
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return

    if amount < 1000:
        await message.answer("❌ Минимум 1 000")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if user is None:
            await message.answer("❌ Сначала /start")
            return

        existing = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if existing is not None:
            await message.answer(
                "❌ Уже есть активный кредит. Сначала погаси:\n"
                f"Долг: <b>{existing.total_due - existing.paid:,}</b>",
                parse_mode="HTML",
            )
            return

        max_loan = calculate_max_loan(user)
        if amount > max_loan:
            await message.answer(
                f"❌ Максимум для тебя — <b>{max_loan:,}</b>\n"
                f"📊 Доверие: {user.trust_score}",
                parse_mode="HTML",
            )
            return

        rate = get_loan_rate(amount)
        term_days = get_loan_term(amount)
        total_due = calculate_total_due(amount)
        due_at = datetime.utcnow() + timedelta(days=term_days)

        user.balance += amount
        user.loan_amount = total_due
        user.loan_due_at = due_at
        user.loans_count += 1
        user.total_borrowed += amount

        session.add(Loan(
            user_id=user.id,
            principal=amount,
            rate=rate,
            total_due=total_due,
            due_at=due_at,
            status="active",
        ))

        await session.commit()
        balance = user.balance

    await message.answer(
        f"✅ <b>Кредит выдан!</b>\n\n"
        f"💵 Получено: <b>{amount:,}</b>\n"
        f"📈 Ставка: <b>{int(rate * 100)}%</b>\n"
        f"💸 К возврату: <b>{total_due:,}</b>\n"
        f"📅 До: <b>{due_at.strftime('%d.%m.%Y')}</b>\n"
        f"💰 Баланс: <b>{balance:,}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ <b>Внимание!</b>\n"
        f"При просрочке:\n"
        f"• Конфискуется 10 карт\n"
        f"• Баланс в минус\n"
        f"• PvP блок на 7 дней\n"
        f"• Trust −15",
        parse_mode="HTML",
    )


# ─── Погасить ───

@router.callback_query(F.data == "bank_repay")
async def cb_bank_repay(query: CallbackQuery) -> None:
    await safe_answer(query)
    await safe_render(
        query,
        "💸 <b>Погашение кредита</b>\n\n"
        "Введи сумму:\n<code>/repay 5000</code>\n\n"
        "💡 При досрочном погашении (7+ дней до срока) — скидка 2%.",
        get_back_menu(),
    )


@router.message(Command("repay"))
async def cmd_repay(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/repay 5000</code>", parse_mode="HTML")
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("❌ Сумма — число")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть > 0")
        return

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if user is None:
            await message.answer("❌ Сначала /start")
            return

        loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if loan is None:
            await message.answer("❌ Нет активного кредита")
            return

        remaining = loan.total_due - loan.paid
        discount = 0
        if is_early_repay(loan):
            discount = early_repay_discount(remaining)
            remaining -= discount

        if amount >= remaining:
            amount = remaining
            closes_loan = True
        else:
            closes_loan = False

        if user.balance < amount:
            await message.answer(
                f"❌ Нужно <b>{amount:,}</b>, у тебя <b>{user.balance:,}</b>",
                parse_mode="HTML",
            )
            return

        user.balance -= amount
        loan.paid += amount

        session.add(LoanPayment(loan_id=loan.id, amount=amount))

        if closes_loan:
            if is_early_repay(loan):
                delta = apply_trust(user, "early_repay")
                event = f"📈 Доверие: +{delta} (досрочно)"
            else:
                delta = apply_trust(user, "on_time")
                event = f"📈 Доверие: +{delta}"

            if loan.principal >= 200_000:
                delta = apply_trust(user, "big_repay")
                event += f"\n💎 Бонус за крупный: +{delta}"

            loan.status = "repaid"
            loan.repaid_at = datetime.utcnow()
            user.loan_amount = 0
            user.loan_due_at = None
            user.loans_repaid += 1

            text = (
                f"✅ <b>Кредит погашен!</b>\n\n"
                f"💸 Списано: <b>{amount:,}</b>\n"
                f"💰 Остаток: <b>{user.balance:,}</b>\n\n"
                f"{event}"
            )
        else:
            left = loan.total_due - loan.paid
            text = (
                f"✅ <b>Платёж принят</b>\n\n"
                f"💸 Списано: <b>{amount:,}</b>\n"
                f"💰 Остаток баланса: <b>{user.balance:,}</b>\n"
                f"⏳ Долг: <b>{left:,}</b>"
            )

        await session.commit()

    await message.answer(text, parse_mode="HTML")


# ─── Рефинансирование ───

@router.callback_query(F.data == "bank_refinance")
async def cb_bank_refinance(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        ok, reason = can_refinance(user)
        if not ok:
            await safe_answer(query, f"❌ {reason}", show_alert=True)
            return

        loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if loan is None:
            await safe_answer(query, "❌ Нет активного кредита", show_alert=True)
            return

        remaining = loan.total_due - loan.paid
        rate = get_loan_rate(remaining)
        total_due = calculate_total_due(remaining)

    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data="bank_refinance_ok")
    b.button(text="🔙 Назад", callback_data=MainMenu(action="bank"))
    b.adjust(1)

    await safe_render(
        query,
        f"📉 <b>Рефинансирование</b>\n\n"
        f"Текущий долг: <b>{remaining:,}</b>\n\n"
        f"Рефинанс — это новый кредит на ту же сумму,\n"
        f"но с новым сроком.\n\n"
        f"📈 Ставка: <b>{int(rate * 100)}%</b>\n"
        f"💸 К возврату: <b>{total_due:,}</b>\n\n"
        f"⚠️ Доверие −3.",
        b.as_markup(),
    )


@router.callback_query(F.data == "bank_refinance_ok")
async def cb_bank_refinance_ok(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if user is None:
            return

        ok, reason = can_refinance(user)
        if not ok:
            await safe_answer(query, f"❌ {reason}", show_alert=True)
            return

        old_loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if old_loan is None:
            await safe_answer(query, "❌ Нет активного кредита", show_alert=True)
            return

        remaining = old_loan.total_due - old_loan.paid
        old_loan.status = "refinanced"
        old_loan.repaid_at = datetime.utcnow()

        rate = get_loan_rate(remaining)
        term_days = get_loan_term(remaining)
        total_due = calculate_total_due(remaining)
        due_at = datetime.utcnow() + timedelta(days=term_days)

        session.add(Loan(
            user_id=user.id,
            principal=remaining,
            rate=rate,
            total_due=total_due,
            due_at=due_at,
            status="active",
            parent_loan_id=old_loan.id,
        ))

        user.loan_amount = total_due
        user.loan_due_at = due_at
        user.last_refinance_at = datetime.utcnow()
        apply_trust(user, "refinance")

        await session.commit()
        trust = user.trust_score

    await safe_render(
        query,
        f"✅ <b>Рефинансировано!</b>\n\n"
        f"💸 Новый долг: <b>{total_due:,}</b>\n"
        f"📈 Ставка: <b>{int(rate * 100)}%</b>\n"
        f"📅 До: <b>{due_at.strftime('%d.%m.%Y')}</b>\n\n"
        f"📉 Доверие: <b>{trust}</b>",
        get_back_menu(),
    )


# ─── История ───

@router.callback_query(F.data == "bank_history")
async def cb_bank_history(query: CallbackQuery) -> None:
    await safe_answer(query)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == query.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            return

        loans = (await session.execute(
            select(Loan)
            .where(Loan.user_id == user.id)
            .order_by(Loan.taken_at.desc())
            .limit(10)
        )).scalars().all()

    if not loans:
        await safe_render(query, "📜 <b>История пуста</b>", get_back_menu())
        return

    status_emoji = {
        "active": "🟡",
        "repaid": "✅",
        "overdue": "🔴",
        "defaulted": "🚫",
        "refinanced": "🔄",
    }

    text = f"📜 <b>История кредитов</b>\n\n"
    for l in loans:
        e = status_emoji.get(l.status, "❔")
        text += (
            f"{e} <b>{l.principal:,}</b> → <b>{l.total_due:,}</b>\n"
            f"    {l.taken_at.strftime('%d.%m.%Y')}"
        )
        if l.repaid_at:
            text += f" — {l.repaid_at.strftime('%d.%m.%Y')}"
        text += "\n\n"

    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=MainMenu(action="bank"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup())


# ═════════════════════════════════════════════
# FAQ ВНУТРИ БАНКА
# ═════════════════════════════════════════════

@router.callback_query(BankFaq.filter())
async def cb_bank_faq(query: CallbackQuery, callback_data: BankFaq) -> None:
    await safe_answer(query)
    topic = callback_data.topic

    if topic == "menu":
        b = InlineKeyboardBuilder()
        b.button(text="💵 Что такое кредит?", callback_data=BankFaq(topic="credit").pack())
        b.button(text="📊 Что такое trust score?", callback_data=BankFaq(topic="trust").pack())
        b.button(text="🎯 Какой у меня лимит?", callback_data=BankFaq(topic="limit").pack())
        b.button(text="📈 Откуда ставка?", callback_data=BankFaq(topic="rate").pack())
        b.button(text="📅 Что такое срок?", callback_data=BankFaq(topic="term").pack())
        b.button(text="💸 Как погасить?", callback_data=BankFaq(topic="repay").pack())
        b.button(text="📉 Что такое рефинансирование?", callback_data=BankFaq(topic="refinance").pack())
        b.button(text="⚠️ Что будет при просрочке?", callback_data=BankFaq(topic="overdue").pack())
        b.button(text="🚨 Что такое дефолт?", callback_data=BankFaq(topic="default").pack())
        b.button(text="🔙 К банку", callback_data=MainMenu(action="bank"))
        b.adjust(1)

        await safe_render(
            query,
            "❓ <b>Банк — как это работает</b>\n\n"
            "Выбери, что хочешь узнать:",
            b.as_markup(),
        )
        return

    texts = {
        "credit": (
            "💵 <b>Что такое кредит?</b>\n\n"
            "Кредит — это деньги, которые банк даёт тебе «в долг».\n\n"
            "<b>Как это работает:</b>\n"
            "1. Ты берёшь сумму — например, 50 000 монет.\n"
            "2. Банк даёт их сразу.\n"
            "3. Через срок ты возвращаешь больше — с процентом.\n\n"
            "<b>Пример:</b>\n"
            "💵 Взял: 50 000\n"
            "📈 Ставка: 15%\n"
            "💸 Вернёшь: 57 500\n\n"
            "<b>Зачем брать:</b>\n"
            "• Купить редкую карту\n"
            "• Участвовать в аукционе\n"
            "• Дропнуть больше карт\n"
            "• Сделать ставку в PvP\n\n"
            "<b>Как взять:</b>\n"
            "<code>/loan 50000</code>\n\n"
            "⚠️ Не бери, если не уверен, что вернёшь."
        ),
        "trust": (
            "📊 <b>Что такое trust score?</b>\n\n"
            "Trust score — это твой «рейтинг доверия» в банке.\n\n"
            "Чем выше — тем больше кредит и лучше условия.\n\n"
            "<b>Ранги:</b>\n"
            "⛔ Чёрный список — ниже 0\n"
            "🥉 Новичок — 0–20\n"
            "🥈 Надёжный — 20–50\n"
            "🥇 Отличный — 50–100\n"
            "💎 Премиум — 100–200\n"
            "👑 Элита банка — 200+\n\n"
            "<b>Как повысить:</b>\n"
            "✅ Погасил в срок — +5\n"
            "✅ Погасил досрочно — +10\n"
            "✅ Крупный кредит погасил — +15\n\n"
            "<b>Как понизить:</b>\n"
            "❌ Просрочка — −15\n"
            "❌ Рефинанс — −3\n"
            "❌ Дефолт — −50\n\n"
            "<b>Зачем нужен:</b>\n"
            "Чем выше — тем больше лимит.\n"
            "От 0: 500 000 монет.\n"
            "От 200: 1 000 000 монет."
        ),
        "limit": (
            "🎯 <b>Твой лимит кредита</b>\n\n"
            "Лимит = 500 000 × множитель.\n\n"
            "<b>Множитель зависит от trust:</b>\n"
            "0–20    → ×1.0\n"
            "20–50   → ×1.2\n"
            "50–100  → ×1.4\n"
            "100–200 → ×1.6\n"
            "200+    → ×1.8–2.0\n\n"
            "<b>Пример:</b>\n"
            "Trust 0 → лимит 500 000\n"
            "Trust 100 → лимит 800 000\n"
            "Trust 200 → лимит 1 000 000\n\n"
            "<b>Как узнать свой:</b>\n"
            "Открой 🏦 Банк — лимит показан вверху."
        ),
        "rate": (
            "📈 <b>Откуда берётся ставка?</b>\n\n"
            "Ставка зависит от суммы кредита.\n\n"
            "<b>Таблица:</b>\n"
            "до 50 000    → 15%\n"
            "до 200 000   → 20%\n"
            "до 500 000   → 25%\n"
            "выше 500 000 → 30%\n\n"
            "<b>Пример:</b>\n"
            "Берёшь 30 000 — ставка 15% → вернёшь 34 500.\n"
            "Берёшь 300 000 — ставка 25% → вернёшь 375 000.\n\n"
            "<b>Логика:</b>\n"
            "Чем больше берёшь — тем выше риск для банка.\n"
            "Тем больше процент.\n\n"
            "💡 Совет: бери минимально нужное."
        ),
        "term": (
            "📅 <b>Что такое срок кредита?</b>\n\n"
            "Срок — это сколько дней у тебя есть на возврат.\n\n"
            "<b>Срок зависит от суммы:</b>\n"
            "до 50 000    → 7 дней\n"
            "до 200 000   → 14 дней\n"
            "до 500 000   → 30 дней\n"
            "выше 500 000 → 45 дней\n\n"
            "<b>Пример:</b>\n"
            "Берёшь 30 000 — вернуть за 7 дней.\n"
            "Берёшь 300 000 — вернуть за 30 дней.\n\n"
            "<b>Что если не успел:</b>\n"
            "Смотри «Что будет при просрочке?»."
        ),
        "repay": (
            "💸 <b>Как погасить кредит?</b>\n\n"
            "<b>Способ 1 — частями:</b>\n"
            "<code>/repay 5000</code>\n"
            "Списывает 5 000 монет в счёт долга.\n\n"
            "<b>Способ 2 — полностью:</b>\n"
            "<code>/repay 999999</code>\n"
            "Спишет всю сумму долга (если хватает).\n\n"
            "<b>Способ 3 — досрочно:</b>\n"
            "Если до срока ≥ 7 дней — скидка 2%.\n\n"
            "<b>Пример:</b>\n"
            "Долг: 57 500\n"
            "Досрочно с скидкой: 56 350\n\n"
            "<b>Что даёт погашение:</b>\n"
            "+5 trust в срок\n"
            "+10 trust досрочно\n"
            "+15 trust за крупный (200k+)"
        ),
        "refinance": (
            "📉 <b>Что такое рефинансирование?</b>\n\n"
            "Рефинанс — это «перезанять» деньги.\n\n"
            "Ты не платишь долг сейчас — ты берёшь НОВЫЙ кредит,\n"
            "который закрывает СТАРЫЙ.\n\n"
            "<b>Пример:</b>\n"
            "Долг: 200 000, срок через 3 дня.\n"
            "Ты не успеваешь вернуть.\n"
            "Рефинанс → новый долг 200 000 + %, срок 30 дней.\n\n"
            "<b>Плюсы:</b>\n"
            "• Больше времени на возврат\n"
            "• Не в просрочку\n\n"
            "<b>Минусы:</b>\n"
            "• Trust −3\n"
            "• Ставка может быть выше\n"
            "• Копится дольше\n\n"
            "<b>Ограничения:</b>\n"
            "• Раз в 3 дня\n"
            "• Только если есть активный кредит"
        ),
        "overdue": (
            "⚠️ <b>Что будет при просрочке?</b>\n\n"
            "Если не вернул в срок — просрочка.\n\n"
            "<b>Что происходит:</b>\n"
            "1. Статус → «просрочка»\n"
            "2. Trust −15\n"
            "3. Даётся 3 дня на погашение\n\n"
            "<b>Если погасил за 3 дня:</b>\n"
            "✅ Кредит закрыт, trust остаётся −15.\n\n"
            "<b>Если не погасил за 3 дня:</b>\n"
            "🚨 Дефолт — смотри следующий раздел.\n\n"
            "<b>Как избежать:</b>\n"
            "• Погаси в срок\n"
            "• Рефинансируй за день до срока"
        ),
        "default": (
            "🚨 <b>Что такое дефолт?</b>\n\n"
            "Дефолт — это когда ты НЕ вернул кредит.\n\n"
            "<b>Что происходит:</b>\n"
            "1. Конфискуются 10 карт (самые дорогие)\n"
            "2. Баланс уходит в минус\n"
            "3. PvP блокируется на 7 дней\n"
            "4. Trust −50\n\n"
            "<b>Пример:</b>\n"
            "Долг: 200 000\n"
            "Карт: 15\n"
            "→ Забирают 10 самых дорогих\n"
            "→ Баланс −150 000 (если было 50 000)\n"
            "→ PvP блок 7 дней\n"
            "→ Trust упадёт до чёрного списка\n\n"
            "<b>Как избежать:</b>\n"
            "• Не бери больше, чем вернёшь\n"
            "• Погашай частями\n"
            "• Рефинансируй"
        ),
    }

    text = texts.get(topic, "❌ Раздел не найден")

    b = InlineKeyboardBuilder()
    b.button(text="🔙 К FAQ", callback_data=BankFaq(topic="menu").pack())
    b.button(text="🏦 К банку", callback_data=MainMenu(action="bank"))
    b.adjust(1)

    await safe_render(query, text, b.as_markup()) 
