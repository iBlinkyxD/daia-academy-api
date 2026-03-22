from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.notification import NotificationType


class NotificationRead(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: str | None
    resource_id: UUID | None
    resource_type: str | None
    is_read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
