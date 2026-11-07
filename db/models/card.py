"""Card, UserCard, Collection, PriceHistory."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Collection(IdMixin, Base):
    __tablename__ = "collections"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    emoji: Mapped[str | None] = mapped_column(String(8), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Card(IdMixin, Base):
    __tablename__ = "cards"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rarity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    team: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0)

    rating: Mapped[int] = mapped_column(Integer, default=0, index=True)

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

    is_sellable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_tradeable: Mapped[bool] = mapped_column(Boolean, default=True)

    collection_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("collections.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    in_drop: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserCard(IdMixin, Base):
    __tablename__ = "user_cards"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    is_iw: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    serial_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    can_sell_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acquired_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    is_cursed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    cursed_debt: Mapped[int] = mapped_column(BigInteger, default=0)


class PriceHistory(IdMixin, Base):
    __tablename__ = "price_history"

    card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
