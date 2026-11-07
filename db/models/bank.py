"""Loan, LoanPayment."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, IdMixin


class Loan(IdMixin, Base):
    __tablename__ = "loans"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True,
    )
    principal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    total_due: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    repaid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    parent_loan_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("loans.id"), nullable=True)


class LoanPayment(IdMixin, Base):
    __tablename__ = "loan_payments"

    loan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("loans.id", ondelete="CASCADE"), index=True,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
