"""Trade, Auction, AuctionBid."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Trade(IdMixin, Base):
    __tablename__ = "trades"

    initiator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    offer_cards: Mapped[str] = mapped_column(Text, default="[]")
    request_cards: Mapped[str] = mapped_column(Text, default="[]")
    offer_money: Mapped[int] = mapped_column(BigInteger, default=0)
    request_money: Mapped[int] = mapped_column(BigInteger, default=0)

    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Auction(IdMixin, Base):
    __tablename__ = "auctions"

    seller_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_card_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user_cards.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )

    start_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    buyout_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_bid: Mapped[int] = mapped_column(BigInteger, default=0)
    current_bidder_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    bid_count: Mapped[int] = mapped_column(Integer, default=0)

    commission_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=10.0)

    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AuctionBid(IdMixin, Base):
    __tablename__ = "auction_bids"

    auction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("auctions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    bidder_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now()) 
