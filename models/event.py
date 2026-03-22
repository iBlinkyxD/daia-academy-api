import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class EventFormat(str, enum.Enum):
    online = "online"
    in_person = "in_person"
    hybrid = "hybrid"


class AttendeeStatus(str, enum.Enum):
    going = "going"
    interested = "interested"
    not_going = "not_going"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    format: Mapped[EventFormat] = mapped_column(Enum(EventFormat), default=EventFormat.online)
    location: Mapped[str | None] = mapped_column(String(300))  # URL or physical address
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    space_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("spaces.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    attendees: Mapped[list["EventAttendee"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class EventAttendee(Base):
    __tablename__ = "event_attendees"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_event_attendee"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[AttendeeStatus] = mapped_column(Enum(AttendeeStatus), default=AttendeeStatus.going)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="events")
    event: Mapped["Event"] = relationship(back_populates="attendees")
