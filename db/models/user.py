"""User, AltAccount."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class User(IdMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    username_normalized: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    balance: Mapped[int] = mapped_column(BigInteger, default=0)

    daily_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_drop_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    season_rating: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    last_dice_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    pvp_wins: Mapped[int] = mapped_column(Integer, default=0)
    pvp_losses: Mapped[int] = mapped_column(Integer, default=0)
    pvp_rating: Mapped[int] = mapped_column(Integer, default=1000, index=True)
    pvp_wins_total: Mapped[int] = mapped_column(Integer, default=0)
    pvp_losses_total: Mapped[int] = mapped_column(Integer, default=0)
    pvp_money_staked: Mapped[int] = mapped_column(BigInteger, default=0)
    pvp_money_won: Mapped[int] = mapped_column(BigInteger, default=0)

    season_titles: Mapped[str] = mapped_column(Text, default="[]")
    best_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seasons_played: Mapped[int] = mapped_column(Integer, default=0)

    ban_level: Mapped[str] = mapped_column(String(16), default="none", index=True)
    ban_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)

    loan_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    loan_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    pvp_blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    loans_count: Mapped[int] = mapped_column(Integer, default=0)
    loans_repaid: Mapped[int] = mapped_column(Integer, default=0)
    total_borrowed: Mapped[int] = mapped_column(BigInteger, default=0)
    last_refinance_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    shop_attempts_today: Mapped[int] = mapped_column(Integer, default=0)
    last_shop_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    referral_count: Mapped[int] = mapped_column(Integer, default=0)

    plus_tier: Mapped[str] = mapped_column(String(16), default="free", index=True)
    plus_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    priority_support: Mapped[bool] = mapped_column(Boolean, default=False)

    can_create_cards: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creator_cards_today: Mapped[int] = mapped_column(Integer, default=0)
    last_creator_card_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    creator_title: Mapped[str | None] = mapped_column(String(32), nullable=True)

    custom_title: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    active_alt_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    support_reputation: Mapped[int] = mapped_column(Integer, default=0)
    tickets_resolved: Mapped[int] = mapped_column(Integer, default=0)
    last_ticket_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)


class AltAccount(IdMixin, Base):
    __tablename__ = "alt_accounts"

    main_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    alt_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
