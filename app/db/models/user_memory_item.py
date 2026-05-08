from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserMemoryItem(Base):
    __tablename__ = "user_memory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    source: Mapped[str] = mapped_column(String, default="inferred", nullable=False)
    confidence: Mapped[float] = mapped_column(default=0.5, nullable=False)
    importance: Mapped[float] = mapped_column(default=0.5, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

