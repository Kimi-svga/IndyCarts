"""AdminRole, Ban, ActionLog, DailyStats."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class AdminRole(IdMixin, Base):
    __tablename__ = "admin_roles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="admin", index=True)
    appointed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    appointed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(256), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Ban(IdMixin, Base):
    __tablename__ = "bans"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
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


class ActionLog(IdMixin, Base):
    __tablename__ = "action_logs"

    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class DailyStats(IdMixin, Base):
    __tablename__ = "daily_stats"

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
