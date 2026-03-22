from uuid import UUID
from pydantic import BaseModel


class BadgeCreate(BaseModel):
    name: str
    description: str | None = None
    icon_url: str | None = None
    criteria: str | None = None

class BadgeRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    icon_url: str | None
    criteria: str | None
    model_config = {"from_attributes": True}
