import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class NotificationType(str, enum.Enum):
    post_like = "post_like"
    comment = "comment"
    new_follower = "new_follower"
    course_update = "course_update"
    badge_awarded = "badge_awarded"
    event_reminder = "event_reminder"
    space_invite = "space_invite"
    message = "message"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))   # ID of the related object
    resource_type: Mapped[str | None] = mapped_column(String(50))               # e.g. "post", "course"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="notifications")
