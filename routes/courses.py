from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import get_db
from models.user import User
from models.course import Course, UserCourse, CourseProgress
from models.module import Module
from models.lesson import Lesson
from models.rating import CourseRating
from schemas.course import CourseCreate, CourseRead, UserCourseRead, CourseProgressRead, LessonRead, ModuleRead, CourseDetailRead, RatingSubmit
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=list[CourseRead])
async def list_courses(db: AsyncSession = Depends(get_db)):
    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    duration_sq = (
        select(func.coalesce(func.sum(Lesson.duration_seconds), 0))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .scalar_subquery()
    )

    enrollment_count_sq = (
        select(func.count(UserCourse.id))
        .where(UserCourse.course_id == Course.id)
        .scalar_subquery()
    )

    avg_rating_sq = (
        select(func.avg(CourseRating.score))
        .where(CourseRating.course_id == Course.id)
        .scalar_subquery()
    )

    review_count_sq = (
        select(func.count(CourseRating.id))
        .where(CourseRating.course_id == Course.id)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            Course,
            lesson_count_sq.label("total_lessons"),
            duration_sq.label("total_duration_seconds"),
            enrollment_count_sq.label("enrollment_count"),
            avg_rating_sq.label("avg_rating"),
            review_count_sq.label("review_count"),
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
        course.enrollment_count = row.enrollment_count or 0
        course.avg_rating = round(float(row.avg_rating), 1) if row.avg_rating else None
        course.review_count = row.review_count or 0
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


@router.get("/enrolled", response_model=list[CourseRead])
async def get_enrolled_courses(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    lesson_count_sq = (
        select(func.count(Lesson.id))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    duration_sq = (
        select(func.coalesce(func.sum(Lesson.duration_seconds), 0))
        .join(Module, Module.id == Lesson.module_id)
        .where(Module.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    enrollment_count_sq = (
        select(func.count(UserCourse.id))
        .where(UserCourse.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    avg_rating_sq = (
        select(func.avg(CourseRating.score))
        .where(CourseRating.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )
    review_count_sq = (
        select(func.count(CourseRating.id))
        .where(CourseRating.course_id == Course.id)
        .correlate(Course)
        .scalar_subquery()
    )

    rows_result = await db.execute(
        select(
            Course,
            lesson_count_sq.label("total_lessons"),
            duration_sq.label("total_duration_seconds"),
            enrollment_count_sq.label("enrollment_count"),
            avg_rating_sq.label("avg_rating"),
            review_count_sq.label("review_count"),
        )
        .join(UserCourse, UserCourse.course_id == Course.id)
        .where(UserCourse.user_id == user.id, Course.is_published == True)
        .order_by(Course.created_at.desc())
    )

    courses = []
    for row in rows_result.all():
        course = row.Course
        course.total_lessons = row.total_lessons or 0
        course.total_duration_seconds = row.total_duration_seconds or 0
        course.enrollment_count = row.enrollment_count or 0
        course.avg_rating = round(float(row.avg_rating), 1) if row.avg_rating else None
        course.review_count = row.review_count or 0
        courses.append(course)

    return courses


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

@router.get("/{slug}", response_model=CourseDetailRead)
async def get_course(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.modules).selectinload(Module.lessons)
        )
        .where(Course.slug == slug, Course.is_published == True)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    count_result = await db.execute(
        select(func.count(UserCourse.id)).where(UserCourse.course_id == course.id)
    )
    course.enrollment_count = count_result.scalar() or 0

    rating_result = await db.execute(
        select(func.avg(CourseRating.score), func.count(CourseRating.id))
        .where(CourseRating.course_id == course.id)
    )
    avg, count = rating_result.one()
    course.avg_rating = round(float(avg), 1) if avg else None
    course.review_count = count or 0

    return course


@router.post("/{slug}/rate", status_code=204)
async def rate_course(
    slug: str,
    payload: RatingSubmit,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if payload.score < 1 or payload.score > 5:
        raise HTTPException(status_code=422, detail="Score must be between 1 and 5")

    course_result = await db.execute(select(Course).where(Course.slug == slug))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await db.execute(
        select(CourseRating).where(
            CourseRating.user_id == user.id, CourseRating.course_id == course.id
        )
    )
    rating = existing.scalar_one_or_none()
    if rating:
        rating.score = payload.score
    else:
        db.add(CourseRating(user_id=user.id, course_id=course.id, score=payload.score))