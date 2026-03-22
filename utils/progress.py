"""
Utility to recompute and persist a user's course progress percentage
after a lesson is marked complete.
"""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.lesson import Lesson, LessonProgress
from models.module import Module
from models.course import CourseProgress


async def recalculate_course_progress(
    db: AsyncSession,
    user_id: UUID,
    course_id: UUID,
) -> float:
    # Total lessons in course
    total_q = (
        select(func.count(Lesson.id))
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    total: int = (await db.execute(total_q)).scalar_one()

    if total == 0:
        return 0.0

    # Completed lessons by this user in this course
    completed_q = (
        select(func.count(LessonProgress.id))
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .where(
            Module.course_id == course_id,
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True,  # noqa: E712
        )
    )
    completed: int = (await db.execute(completed_q)).scalar_one()

    pct = round((completed / total) * 100, 2)

    # Upsert CourseProgress
    result = await db.execute(
        select(CourseProgress).where(
            CourseProgress.user_id == user_id,
            CourseProgress.course_id == course_id,
        )
    )
    cp = result.scalar_one_or_none()
    if cp:
        cp.progress_pct = pct
        cp.last_accessed = datetime.now(timezone.utc)
    else:
        db.add(CourseProgress(
            user_id=user_id,
            course_id=course_id,
            progress_pct=pct,
            last_accessed=datetime.now(timezone.utc),
        ))

    return pct
