"""PvpBattle, PvpStake, PvpSeason, SeasonReward, UserSeasonStat."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class PvpSeason(IdMixin, Base):
    __tablename__ = "pvp_seasons"

    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    top10_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PvpBattle(IdMixin, Base):
    __tablename__ = "pvp_battles"

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


class PvpStake(IdMixin, Base):
    __tablename__ = "pvp_stakes"

    battle_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pvp_battles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    user_card_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_cards.id"), nullable=False)
    side: Mapped[str] = mapped_column(String(16))

    __table_args__ = (UniqueConstraint("battle_id", "user_card_id", name="uq_pvp_stake_card"),)


class SeasonReward(IdMixin, Base):
    __tablename__ = "season_rewards"

    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pvp_seasons.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0)
    reward_attempts: Mapped[int] = mapped_column(Integer, default=0)
    reward_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (UniqueConstraint("season_id", "position", name="uq_season_position"),)


class UserSeasonStat(IdMixin, Base):
    __tablename__ = "user_season_stats"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pvp_seasons.id", ondelete="CASCADE"),
        nullable=False,
    )
    final_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reward_received: Mapped[int] = mapped_column(BigInteger, default=0)

    __table_args__ = (UniqueConstraint("user_id", "season_id", name="uq_user_season"),)
