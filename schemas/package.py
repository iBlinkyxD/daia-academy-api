from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from schemas.course import CourseRead


class PackageCourseItem(BaseModel):
    id: str
    title: str
    image: str | None
    courseNumber: str
    model_config = {"from_attributes": True}


class PackageRead(BaseModel):
    id: UUID
    title: str
    slug: str
    short_description: str | None
    level: str | None
    courses: list[PackageCourseItem] = []
    created_at: datetime
    model_config = {"from_attributes": True}