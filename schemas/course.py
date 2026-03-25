from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from models.course import CourseLevel, EnrollmentStatus


class RatingSubmit(BaseModel):
    score: int  # 1–5


class CourseCreate(BaseModel):
    title: str
    slug: str
    description: str | None = None
    thumbnail_url: str | None = None
    level: CourseLevel = CourseLevel.beginner
    instructor_id: UUID | None = None


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
    duration_seconds: int | None
    position: int
    model_config = {"from_attributes": True}

class ModuleRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    position: int
    lessons: list[LessonRead] = []
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