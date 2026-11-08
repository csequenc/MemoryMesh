
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class MemoryModel(Base):
    __tablename__ = "memories"

    memory_id: Mapped[str] = mapped_column(
        String(36), primary_key=True
    )

    subject: Mapped[str] = mapped_column(String, nullable=False)
    predicate: Mapped[str] = mapped_column(String, nullable=False)
    object_value: Mapped[str] = mapped_column(String, nullable=False)
    context: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    source_id: Mapped[str] = mapped_column(String, nullable=False)

    confidence: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
