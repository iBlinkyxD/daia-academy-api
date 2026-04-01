from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.lesson import LessonType


class LessonCreate(BaseModel):
    module_id: UUID
    title: str
    content: str | None = None
    narration_script: str | None = None
    video_url: str | None = None
    duration_seconds: int | None = None
    lesson_type: LessonType = LessonType.article
    position: int = 0
    objectives: list | None = None
    vocabulary: list | None = None

class LessonRead(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    content: str | None
    video_url: str | None
    duration_seconds: int | None
    lesson_type: LessonType
    position: int
    created_at: datetime
    model_config = {"from_attributes": True}

class LessonUpdate(BaseModel):
    content: str | None = None
    narration_script: str | None = None
    objectives: list | None = None
    vocabulary: list | None = None

class LessonProgressUpdate(BaseModel):
    completed: bool
    last_position_seconds: int | None = None

class LessonProgressRead(BaseModel):
    lesson_id: UUID
    completed: bool
    completed_at: datetime | None
    last_position_seconds: int | None
    model_config = {"from_attributes": True}
