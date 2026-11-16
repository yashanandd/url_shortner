import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, Date, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    short_code: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    referrer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    ip_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    device_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    browser: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    os: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_click_events_code_time", "short_code", "clicked_at"),
    )


class AnalyticsAggregate(Base):
    __tablename__ = "analytics_aggregates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    short_code: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )
    total_clicks: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    unique_visitors: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    desktop_clicks: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    mobile_clicks: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )
    tablet_clicks: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("short_code", "date", name="uq_short_code_date"),
        Index("ix_aggregates_code_date", "short_code", "date"),
    )
