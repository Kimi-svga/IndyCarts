"""Badge, UserBadge."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Badge(IdMixin, Base):
    __tablename__ = "badges"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)


class UserBadge(IdMixin, Base):
    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    badge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    awarded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)
