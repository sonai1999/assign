
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    """Stores product inventory details."""

    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    warehouse_location: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    base_price_usd: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )


class ReconciliationAuditLog(Base):
    """Stores reconciliation job outcomes."""

    __tablename__ = "reconciliation_audit_logs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCESS', 'RETRY_FALLBACK', 'FAILED')",
            name="ck_audit_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    skus_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
