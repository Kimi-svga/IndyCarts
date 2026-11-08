"""Subscription, SubscriptionPayment, PlusReward."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Subscription(IdMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, index=True,
    )
    tier: Mapped[str] = mapped_column(String(16), default="free", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    total_paid_stars: Mapped[int] = mapped_column(Integer, default=0)
    total_paid_coins: Mapped[int] = mapped_column(BigInteger, default=0)
    renewals_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SubscriptionPayment(IdMixin, Base):
    __tablename__ = "subscription_payments"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True,
    )
    method: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column(BigInteger)
    stars_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    telegram_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class PlusReward(IdMixin, Base):
    __tablename__ = "plus_rewards"

    month: Mapped[str] = mapped_column(String(7), unique=True)
    card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    money: Mapped[int] = mapped_column(BigInteger, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
