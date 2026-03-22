import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon_url: Mapped[str | None] = mapped_column(String(500))
    criteria: Mapped[str | None] = mapped_column(Text)  # Human-readable criteria

    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="badge")
