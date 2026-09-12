from datetime import datetime, date
from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    username_normalized: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    balance: Mapped[int] = mapped_column(BigInteger, default=0)

    rating_common: Mapped[int] = mapped_column(Integer, default=0)
    rating_rare: Mapped[int] = mapped_column(Integer, default=0)
    rating_epic: Mapped[int] = mapped_column(Integer, default=0)
    rating_legendary: Mapped[int] = mapped_column(Integer, default=0)
    rating_ultra: Mapped[int] = mapped_column(Integer, default=0)
    rating_iw: Mapped[int] = mapped_column(Integer, default=0)
    rating_season: Mapped[int] = mapped_column(Integer, default=0)
    rating_total: Mapped[int] = mapped_column(Integer, default=0)

    pvp_wins: Mapped[int] = mapped_column(Integer, default=0)
    pvp_losses: Mapped[int] = mapped_column(Integer, default=0)

    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rarity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_iw: Mapped[bool] = mapped_column(Boolean, default=False)
    team: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    base_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    floor_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ceiling_price: Mapped[int] = mapped_column(BigInteger, nullable=False)

    image_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    drop_weight: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserCard(Base):
    __tablename__ = "user_cards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=False, index=True)

    acquired_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acquired_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    is_listed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    listed_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    balance_after: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class DailyReward(Base):
    __tablename__ = "daily_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    reward_date: Mapped[date] = mapped_column(Date, nullable=False)
    money: Mapped[int] = mapped_column(BigInteger, default=450)
    attempts: Mapped[int] = mapped_column(Integer, default=2)
    claimed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "reward_date", name="uq_daily_user_date"),)


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    term_days: Mapped[int] = mapped_column(Integer, nullable=False)
    total_due: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PvpBattle(Base):
    __tablename__ = "pvp_battles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    challenger_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    opponent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    challenger_roll: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_roll: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winner_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    fee: Mapped[int] = mapped_column(BigInteger, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
