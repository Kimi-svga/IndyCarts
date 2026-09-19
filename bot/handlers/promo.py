"""Промокоды."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from db.models import Card, PromoActivation, PromoCode, User, UserCard
from db.session import AsyncSessionLocal

router = Router()


class PromoState(StatesGroup):
    """Ожидание кода."""
    waiting_for_code = State()


@router.message(Command("promo"))
async def cmd_promo(message: Message, state: FSMContext) -> None:
    """Запрашивает код."""
    await message.answer("🎁 Введи промокод:")
    await state.set_state(PromoState.waiting_for_code)


@router.message(PromoState.waiting_for_code)
async def check_promo(message: Message, state: FSMContext) -> None:
    """Проверяет и активирует промокод."""
    code = message.text.strip().upper()
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )).scalar_one_or_none()

        if user is None:
            await message.answer("❌ Сначала /start")
            return

        promo = (await session.execute(
            select(PromoCode).where(
                PromoCode.code == code,
                PromoCode.is_active == True,
            )
        )).scalar_one_or_none()

        if promo is None:
            await message.answer("❌ Промокод не найден")
            return

        if promo.max_activations and promo.activations >= promo.max_activations:
            await message.answer("❌ Промокод исчерпан")
            return

        already = (await session.execute(
            select(PromoActivation).where(
                PromoActivation.promo_id == promo.id,
                PromoActivation.user_id == user.id,
            )
        )).scalar_one_or_none()

        if already is not None:
            await message.answer("❌ Ты уже активировал")
            return

        user.balance += promo.reward_money
        user.daily_attempts += promo.reward_attempts
        promo.activations += 1
        session.add(PromoActivation(promo_id=promo.id, user_id=user.id))

        card_text = ""
        if promo.reward_card_id is not None:
            card = (await session.execute(
                select(Card).where(Card.id == promo.reward_card_id)
            )).scalar_one_or_none()

            if card is not None:
                session.add(UserCard(
                    user_id=user.id,
                    card_id=card.id,
                    acquired_price=card.current_price,
                ))
                card_text = f"\n🎴 + {card.name}"

        await session.commit()
        money = promo.reward_money
        attempts = promo.reward_attempts

    await message.answer(f"✅ Активирован!\n💰 +{money}\n🎴 +{attempts}{card_text}") 
