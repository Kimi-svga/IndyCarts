from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import User, PromoCode, PromoActivation

router = Router()

class PromoState(StatesGroup):
    waiting_for_code = State()

@router.message(Command("promo"))
async def cmd_promo(message: Message, state: FSMContext):
    await message.answer("🎁 Введи промокод:")
    await state.set_state(PromoState.waiting_for_code)

@router.message(PromoState.waiting_for_code)
async def check_promo(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        if not user:
            await message.answer("❌ Сначала /start")
            return
        promo = (await session.execute(select(PromoCode).where(PromoCode.code == code, PromoCode.is_active == True))).scalar_one_or_none()
        if not promo:
            await message.answer("❌ Промокод не найден")
            return
        if promo.max_activations and promo.activations >= promo.max_activations:
            await message.answer("❌ Промокод исчерпан")
            return
        already = (await session.execute(select(PromoActivation).where(PromoActivation.promo_id == promo.id, PromoActivation.user_id == user.id))).scalar_one_or_none()
        if already:
            await message.answer("❌ Ты уже активировал")
            return
        user.balance += promo.reward_money
        user.daily_attempts += promo.reward_attempts
        promo.activations += 1
        session.add(PromoActivation(promo_id=promo.id, user_id=user.id))
        await session.commit()
        money, attempts = promo.reward_money, promo.reward_attempts
    await message.answer(f"✅ Активирован!\n💰 +{money}\n🎴 +{attempts}") 
