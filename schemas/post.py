from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.post import PostVisibility


class PostCreate(BaseModel):
    space_id: UUID | None = None
    title: str | None = None
    content: str
    media_url: str | None = None
    visibility: PostVisibility = PostVisibility.public

class PostRead(BaseModel):
    id: UUID
    author_id: UUID
    space_id: UUID | None
    title: str | None
    content: str
    media_url: str | None
    visibility: PostVisibility
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}

class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    visibility: PostVisibility | None = None
