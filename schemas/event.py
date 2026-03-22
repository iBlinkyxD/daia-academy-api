from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.event import EventFormat, AttendeeStatus


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    cover_url: str | None = None
    format: EventFormat = EventFormat.online
    location: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    space_id: UUID | None = None

class EventRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    cover_url: str | None
    format: EventFormat
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    space_id: UUID | None
    created_by: UUID
    created_at: datetime
    model_config = {"from_attributes": True}

class AttendeeStatusUpdate(BaseModel):
    status: AttendeeStatus
