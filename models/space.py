import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class SpaceVisibility(str, enum.Enum):
    public = "public"
    private = "private"
    invite_only = "invite_only"


class SpaceMemberRole(str, enum.Enum):
    member = "member"
    moderator = "moderator"
    admin = "admin"


class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    visibility: Mapped[SpaceVisibility] = mapped_column(
        Enum(SpaceVisibility), default=SpaceVisibility.public, nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    members: Mapped[list["UserSpace"]] = relationship(back_populates="space", cascade="all, delete-orphan")
    posts: Mapped[list["Post"]] = relationship(back_populates="space", cascade="all, delete-orphan")


class UserSpace(Base):
    """Junction table: user ↔ space (replaces joinedSpaces[] array)."""
    __tablename__ = "user_spaces"
    __table_args__ = (UniqueConstraint("user_id", "space_id", name="uq_user_space"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    space_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[SpaceMemberRole] = mapped_column(
        Enum(SpaceMemberRole), default=SpaceMemberRole.member, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="spaces")
    space: Mapped["Space"] = relationship(back_populates="members")
