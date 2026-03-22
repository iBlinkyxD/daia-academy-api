from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ModuleCreate(BaseModel):
    course_id: UUID
    title: str
    description: str | None = None
    position: int = 0

class ModuleRead(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    position: int
    created_at: datetime
    model_config = {"from_attributes": True}
