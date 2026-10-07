"""Модели SQLAlchemy для Indy Carts."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, func,
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
    last_drop_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    # Creator (1.2.0)
    can_create_cards: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creator_cards_today: Mapped[int] = mapped_column(Integer, default=0)
    last_creator_card_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    creator_title: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Friends (1.3.0)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Support
    support_reputation: Mapped[int] = mapped_column(Integer, default=0)
    tickets_resolved: Mapped[int] = mapped_column(Integer, default=0)
    last_ticket_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    is_plus_only: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_creator_card: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creator_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserCard(Base):
    __tablename__ = "user_cards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)

    is_iw: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
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

    money_stake: Mapped[int] = mapped_column(BigInteger, default=0)
    season_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("pvp_seasons.id"), nullable=True, index=True)
    challenger_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    opponent_ready: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PvpStake(Base):
    __tablename__ = "pvp_stakes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    battle_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pvp_battles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user_card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_cards.id"), nullable=False)
    side: Mapped[str] = mapped_column(String(16))


class PvpSeason(Base):
    __tablename__ = "pvp_seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    top10_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SeasonReward(Base):
    __tablename__ = "season_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pvp_seasons.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0)
    reward_attempts: Mapped[int] = mapped_column(Integer, default=0)
    reward_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (UniqueConstraint("season_id", "position", name="uq_season_position"),)


class UserSeasonStat(Base):
    __tablename__ = "user_season_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    season_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pvp_seasons.id", ondelete="CASCADE"), nullable=False)
    final_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reward_received: Mapped[int] = mapped_column(BigInteger, default=0)

    __table_args__ = (UniqueConstraint("user_id", "season_id", name="uq_user_season"),)


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


class PvpReward(Base):
    __tablename__ = "pvp_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    position: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0)
    reward_attempts: Mapped[int] = mapped_column(Integer, default=0)
    reward_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="admin", index=True)
    appointed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    appointed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(256), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Ban(Base):
    __tablename__ = "bans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(256), nullable=False)
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    is_permanent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lifted_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    users_total: Mapped[int] = mapped_column(Integer, default=0)
    users_new: Mapped[int] = mapped_column(Integer, default=0)
    users_active: Mapped[int] = mapped_column(Integer, default=0)
    money_total: Mapped[int] = mapped_column(BigInteger, default=0)
    money_in: Mapped[int] = mapped_column(BigInteger, default=0)
    money_out: Mapped[int] = mapped_column(BigInteger, default=0)
    cards_in_play: Mapped[int] = mapped_column(Integer, default=0)
    cards_dropped: Mapped[int] = mapped_column(Integer, default=0)
    pvp_battles: Mapped[int] = mapped_column(Integer, default=0)
    plus_active: Mapped[int] = mapped_column(Integer, default=0)
    plus_new: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
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


class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    method: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column(BigInteger)
    stars_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    telegram_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class PlusReward(Base):
    __tablename__ = "plus_rewards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(7), unique=True)
    card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    money: Mapped[int] = mapped_column(BigInteger, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    principal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    total_due: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    repaid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parent_loan_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("loans.id"), nullable=True)


class LoanPayment(Base):
    __tablename__ = "loan_payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    loan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("loans.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


# ═════════════════════════════════════════════
# FRIENDS (1.3.0)
# ═════════════════════════════════════════════

class Friend(Base):
    __tablename__ = "friends"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    friend_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="uq_friend_pair"),)


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_freq_pair"),)

# ═════════════════════════════════════════════
# TRADE + AUCTION (1.3.1 + 1.3.2)
# ═════════════════════════════════════════════

class Trade(Base):
    """Обмен картами между игроками."""
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    initiator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    offer_cards: Mapped[str] = mapped_column(Text, default="[]")
    request_cards: Mapped[str] = mapped_column(Text, default="[]")
    offer_money: Mapped[int] = mapped_column(BigInteger, default=0)
    request_money: Mapped[int] = mapped_column(BigInteger, default=0)

    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Auction(Base):
    """Лот на аукционе."""
    __tablename__ = "auctions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_cards.id", ondelete="CASCADE"), unique=True, nullable=False)

    start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    buyout_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_bid: Mapped[int] = mapped_column(BigInteger, default=0)
    current_bidder_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    bid_count: Mapped[int] = mapped_column(Integer, default=0)

    commission_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=10.0)

    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuctionBid(Base):
    """Ставка на аукционе."""
    __tablename__ = "auction_bids"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    auction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("auctions.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
