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
    daily_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pvp_wins: Mapped[int] = mapped_column(Integer, default=0)
    pvp_losses: Mapped[int] = mapped_column(Integer, default=0)
    loan_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    loan_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    shop_attempts_today: Mapped[int] = mapped_column(Integer, default=0)
    last_shop_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_drop_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rarity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    team: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)
    base_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    floor_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ceiling_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    image_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    drop_weight: Mapped[int] = mapped_column(Integer, default=100)
    max_supply: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issued: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserCard(Base):
    __tablename__ = "user_cards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    is_iw: Mapped[bool] = mapped_column(Boolean, default=False)
    serial_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    can_sell_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acquired_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class PvpBattle(Base):
    __tablename__ = "pvp_battles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    challenger_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    opponent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    challenger_roll: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_roll: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winner_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DailyReward(Base):
    __tablename__ = "daily_rewards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_date: Mapped[date] = mapped_column(Date, nullable=False)
    money: Mapped[int] = mapped_column(BigInteger, default=450)
    attempts: Mapped[int] = mapped_column(Integer, default=2)
    claimed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("user_id", "reward_date", name="uq_daily_user_date"),)


class PromoCode(Base):
    __tablename__ = "promocodes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0)
    reward_attempts: Mapped[int] = mapped_column(Integer, default=0)
    reward_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    max_activations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activations: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PromoActivation(Base):
    __tablename__ = "promo_activations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    promo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("promocodes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("promo_id", "user_id", name="uq_promo_user"),)


class Reward(Base):
    __tablename__ = "rewards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    position: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    reward_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reward_value: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdminRole(Base):
    __tablename__ = "admin_roles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="admin")
    appointed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    appointed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now()) 
