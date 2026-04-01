import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Enum, Float, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class CourseLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    dropped = "dropped"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    faq: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructor_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    badge_url: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[CourseLevel] = mapped_column(Enum(CourseLevel), default=CourseLevel.beginner)
    instructor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    modules: Mapped[list["Module"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Module.position"
    )
    enrollments: Mapped[list["UserCourse"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    progress_records: Mapped[list["CourseProgress"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["CourseRating"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class UserCourse(Base):
    __tablename__ = "user_courses"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_user_course"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.active, nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")


class CourseProgress(Base):
    __tablename__ = "course_progress"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_course_progress"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="course_progress")
    course: Mapped["Course"] = relationship(back_populates="progress_records")