import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database import Base


class LessonType(str, enum.Enum):
    video = "video"
    article = "article"
    quiz = "quiz"
    assignment = "assignment"


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)           # Markdown / HTML body
    narration_script: Mapped[str | None] = mapped_column(Text)  # Spoken narration
    video_url: Mapped[str | None] = mapped_column(String(500))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), default=LessonType.article)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    objectives: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    vocabulary: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    module: Mapped["Module"] = relationship(back_populates="lessons")
    progress_records: Mapped[list["LessonProgress"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class LessonProgress(Base):
    """Per-user per-lesson completion tracking."""
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_position_seconds: Mapped[int | None] = mapped_column(Integer)  # Video resume point

    user: Mapped["User"] = relationship(back_populates="lesson_progress")
    lesson: Mapped["Lesson"] = relationship(back_populates="progress_records")
