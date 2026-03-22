from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.chat import ChatType


class ChatCreate(BaseModel):
    name: str | None = None
    chat_type: ChatType = ChatType.direct
    space_id: UUID | None = None
    participant_ids: list[UUID] = []

class ChatRead(BaseModel):
    id: UUID
    name: str | None
    chat_type: ChatType
    space_id: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}

class MessageCreate(BaseModel):
    content: str
    media_url: str | None = None

class MessageRead(BaseModel):
    id: UUID
    chat_id: UUID
    sender_id: UUID
    content: str
    media_url: str | None
    is_deleted: bool
    created_at: datetime
    model_config = {"from_attributes": True}
