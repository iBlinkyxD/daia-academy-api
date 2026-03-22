import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class PostVisibility(str, enum.Enum):
    public = "public"
    space_only = "space_only"
    draft = "draft"


class Post(Base):
    """
    No authorName/authorAvatar — those are fetched from DAIA API via author_id.
    No spaceName — fetched via space FK join.
    No likes_count / comments_count — computed via SQL COUNT().
    """
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    space_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("spaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500))
    visibility: Mapped[PostVisibility] = mapped_column(
        Enum(PostVisibility), default=PostVisibility.public, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    author: Mapped["User"] = relationship(back_populates="posts")
    space: Mapped["Space | None"] = relationship(back_populates="posts")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="post_likes")
    post: Mapped["Post"] = relationship(back_populates="likes")
