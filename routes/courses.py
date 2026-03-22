from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.user import User
from models.course import Course, UserCourse, CourseProgress
from models.module import Module
from models.lesson import Lesson
from schemas.course import CourseCreate, CourseRead, UserCourseRead, CourseProgressRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=list[CourseRead])
async def list_courses(db: AsyncSession = Depends(get_db)):
    # Correlated subquery: count lessons per course
    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    # Correlated subquery: sum duration_seconds per course
    duration_sq = (
        select(func.coalesce(func.sum(Lesson.duration_seconds), 0))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            Course,
            lesson_count_sq.label("total_lessons"),
            duration_sq.label("total_duration_seconds"),
        )
        .where(Course.is_published == True)
        .order_by(Course.created_at.desc())
    )

    rows = result.all()

    courses = []
    for row in rows:
        course = row.Course
        course.total_lessons = row.total_lessons or 0
        course.total_duration_seconds = row.total_duration_seconds or 0
        courses.append(course)

    return courses


@router.post("/", response_model=CourseRead, status_code=201)
async def create_course(
    payload: CourseCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    course = Course(**payload.model_dump(), created_by=user.id)
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.post("/{course_id}/enroll", response_model=UserCourseRead, status_code=201)
async def enroll(
    course_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    enrollment = UserCourse(user_id=user.id, course_id=course_id)
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.get("/{course_id}/progress", response_model=CourseProgressRead)
async def get_progress(
    course_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    res = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user.id, CourseProgress.course_id == course_id
        )
    )
    progress = res.scalar_one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="No progress yet")
    return progress
