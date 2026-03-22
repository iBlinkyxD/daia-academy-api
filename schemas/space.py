from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.space import SpaceVisibility, SpaceMemberRole


class SpaceCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    cover_url: str | None = None
    visibility: SpaceVisibility = SpaceVisibility.public

class SpaceRead(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    cover_url: str | None
    visibility: SpaceVisibility
    created_by: UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}

class UserSpaceRead(BaseModel):
    space_id: UUID
    role: SpaceMemberRole
    joined_at: datetime
    model_config = {"from_attributes": True}
