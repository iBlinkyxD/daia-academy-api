import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class User(Base):
    """
    Reference shadow of the DAIA main API user.
    Only stores the user_id (from DAIA API) and Academy-specific fields.
    All profile data (name, email, avatar) lives in the DAIA API.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Foreign reference to DAIA API user — logical FK only (different DB)
    daia_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    interests: Mapped[list["UserInterest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    spaces: Mapped[list["UserSpace"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    post_likes: Mapped[list["PostLike"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    enrollments: Mapped[list["UserCourse"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    course_progress: Mapped[list["CourseProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    lesson_progress: Mapped[list["LessonProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    events: Mapped[list["EventAttendee"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_memberships: Mapped[list["ChatParticipant"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="sender", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    ratings: Mapped[list["CourseRating"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activities: Mapped[list["UserActivity"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserInterest(Base):
    """Replaces the interests[] array — normalized into rows."""
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest", name="uq_user_interest"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interest: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped["User"] = relationship(back_populates="interests")


class UserBadge(Base):
    """Junction table: user ↔ badge (many-to-many)."""
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")
