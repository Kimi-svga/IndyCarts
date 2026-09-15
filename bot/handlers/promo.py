from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from db.session import AsyncSessionLocal
from db.models import User, PromoCode, PromoActivation

router = Router()


@router.message(Command("promo"))
async def cmd_promo(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🎁 Использование: <code>/promo КОД</code>", parse_mode="HTML")
        return

    code = parts[1].strip().upper()

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        user = (await session.execute(stmt)).scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала /start")
            return

        stmt = select(PromoCode).where(PromoCode.code == code, PromoCode.is_active == True)
        promo = (await session.execute(stmt)).scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден")
            return

        if promo.max_activations and promo.activations >= promo.max_activations:
            await message.answer("❌ Промокод исчерпан")
            return

        stmt = select(PromoActivation).where(
            PromoActivation.promo_id == promo.id,
            PromoActivation.user_id == user.id,
        )
        if (await session.execute(stmt)).scalar_one_or_none():
            await message.answer("❌ Ты уже активировал этот промокод")
            return

        user.balance += promo.reward_money
        user.daily_attempts += promo.reward_attempts
        promo.activations += 1
        session.add(PromoActivation(promo_id=promo.id, user_id=user.id))
        await session.commit()

    await message.answer(
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"💰 +{promo.reward_money} монет\n"
        f"🎴 +{promo.reward_attempts} попыток",
        parse_mode="HTML"
    )
