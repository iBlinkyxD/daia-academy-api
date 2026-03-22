import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class ChatType(str, enum.Enum):
    direct = "direct"
    group = "group"
    space = "space"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(String(150))  # For group chats
    chat_type: Mapped[ChatType] = mapped_column(Enum(ChatType), default=ChatType.direct, nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("spaces.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    participants: Mapped[list["ChatParticipant"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class ChatParticipant(Base):
    """Junction table: user ↔ chat (many-to-many)."""
    __tablename__ = "chat_participants"
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_chat_participant"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="chat_memberships")
    chat: Mapped["Chat"] = relationship(back_populates="participants")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chat: Mapped["Chat"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="messages")
