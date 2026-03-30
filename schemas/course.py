from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from models.course import CourseLevel, EnrollmentStatus
from models.lesson import LessonType


class RatingSubmit(BaseModel):
    score: int  # 1–5


class CourseCreate(BaseModel):
    title: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    thumbnail_url: str | None = None
    badge_url: str | None = None
    level: CourseLevel = CourseLevel.beginner
    instructor_id: UUID | None = None
    instructor_name: str | None = None
    code: str | None = None
    is_published: bool = False


class CourseRead(BaseModel):
    id: UUID
    title: str
    slug: str
    code: str | None
    description: str | None
    thumbnail_url: str | None
    badge_url: str | None = None
    level: CourseLevel
    instructor_id: UUID | None
    instructor_name: str | None
    is_published: bool
    total_lessons: int = 0
    total_duration_seconds: int = 0
    enrollment_count: int = 0
    avg_rating: float | None = None
    review_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class UserCourseRead(BaseModel):
    course_id: UUID
    status: EnrollmentStatus
    enrolled_at: datetime
    completed_at: datetime | None
    model_config = {"from_attributes": True}


class CourseProgressRead(BaseModel):
    course_id: UUID
    progress_pct: float
    last_accessed: datetime | None
    updated_at: datetime
    model_config = {"from_attributes": True}

class LessonRead(BaseModel):
    id: UUID
    title: str
    duration_seconds: int | None = None
    position: int
    content: str | None = None
    video_url: str | None = None
    lesson_type: LessonType | None = None
    objectives: list[Any] | None = None
    vocabulary: list[Any] | None = None
    model_config = {"from_attributes": True}

class ModuleRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    position: int
    lessons: list[LessonRead] = []
    model_config = {"from_attributes": True}

class AdminCourseRead(BaseModel):
    id: UUID
    title: str
    slug: str
    code: str | None
    short_description: str | None
    thumbnail_url: str | None
    badge_url: str | None
    is_published: bool
    module_count: int = 0
    total_lessons: int = 0
    has_video: bool = False
    enrollment_count: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}


class CourseDetailRead(BaseModel):
    id: UUID
    title: str
    slug: str
    code: str | None
    description: str | None
    short_description: str | None
    thumbnail_url: str | None
    level: CourseLevel
    instructor_id: UUID | None
    instructor_name: str | None
    is_published: bool
    modules: list[ModuleRead] = []
    enrollment_count: int = 0
    avg_rating: float | None = None
    review_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}