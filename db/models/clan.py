"""Clan, ClanMember, ClanLog, ClanInvite."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Clan(IdMixin, Base):
    __tablename__ = "clans"

    name: Mapped[str] = mapped_column(String(24), unique=True, nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(4), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    level: Mapped[int] = mapped_column(Integer, default=1, index=True)
    xp: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    treasury: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )

    is_open: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(),
    )


class ClanMember(IdMixin, Base):
    __tablename__ = "clan_members"

    clan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )

    role: Mapped[str] = mapped_column(String(16), default="member", index=True)
    contribution: Mapped[int] = mapped_column(BigInteger, default=0)

    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("clan_id", "user_id", name="uq_clan_member"),)


class ClanLog(IdMixin, Base):
    __tablename__ = "clan_logs"

    clan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True,
    )


class ClanInvite(IdMixin, Base):
    __tablename__ = "clan_invites"

    clan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    from_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    to_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("clan_id", "to_user_id", "status", name="uq_clan_invite_pending"),
    )
