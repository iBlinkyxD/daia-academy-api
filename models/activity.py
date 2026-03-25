import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database import Base


class ActivityType(str, enum.Enum):
    lesson_completed   = "lesson_completed"
    badge_earned       = "badge_earned"
    course_enrolled    = "course_enrolled"
    package_enrolled   = "package_enrolled"
    post_created       = "post_created"
    post_liked         = "post_liked"
    post_commented     = "post_commented"
    user_followed      = "user_followed"


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    user: Mapped["User"] = relationship(back_populates="activities")