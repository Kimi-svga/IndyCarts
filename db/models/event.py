"""Event, EventAttempt, CreatorCard, ModerationLog, RoyaltyPayout."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Event(IdMixin, Base):
    __tablename__ = "events"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), default="riddle")
    riddle: Mapped[str | None] = mapped_column(Text, nullable=True)
    riddle_image: Mapped[str | None] = mapped_column(String(256), nullable=True)
    answer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    answer_hint: Mapped[str | None] = mapped_column(String(256), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    phase: Mapped[str] = mapped_column(String(32), default="active", index=True)
    max_winners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winners_count: Mapped[int] = mapped_column(Integer, default=0)
    grant_creator: Mapped[bool] = mapped_column(Boolean, default=False)
    grant_money: Mapped[int] = mapped_column(BigInteger, default=0)
    grant_attempts: Mapped[int] = mapped_column(Integer, default=0)
    grant_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EventAttempt(IdMixin, Base):
    __tablename__ = "event_attempts"

    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    answer: Mapped[str] = mapped_column(String(64), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CreatorCard(IdMixin, Base):
    __tablename__ = "creator_cards"

    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cards.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    royalty_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=5.0)
    total_earned: Mapped[int] = mapped_column(BigInteger, default=0)
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    moderation_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    moderated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ModerationLog(IdMixin, Base):
    __tablename__ = "moderation_logs"

    creator_card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("creator_cards.id", ondelete="CASCADE"), nullable=False,
    )
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RoyaltyPayout(IdMixin, Base):
    __tablename__ = "royalty_payouts"

    creator_card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("creator_cards.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    buyer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    sale_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    royalty_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True) 
