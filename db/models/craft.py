"""CraftRecipe."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class CraftRecipe(IdMixin, Base):
    __tablename__ = "craft_recipes"

    result_card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ingredients: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now()) 
