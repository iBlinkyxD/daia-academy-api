from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class CommentCreate(BaseModel):
    post_id: UUID
    content: str
    parent_id: UUID | None = None

class CommentRead(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID
    parent_id: UUID | None
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}
