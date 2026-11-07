"""Quest, UserQuest."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Quest(IdMixin, Base):
    __tablename__ = "quests"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    quest_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_money: Mapped[int] = mapped_column(BigInteger, default=0)
    reward_attempts: Mapped[int] = mapped_column(Integer, default=0)
    reward_card_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("cards.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserQuest(IdMixin, Base):
    __tablename__ = "user_quests"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    quest_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    claimed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),)
