from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.lesson import Lesson, LessonProgress
from models.module import Module
from schemas.lesson import LessonCreate, LessonUpdate, LessonRead, LessonProgressUpdate, LessonProgressRead
from utils.auth import get_current_user_id
from utils.progress import recalculate_course_progress
from routes.activities import log_activity
from models.activity import ActivityType

router = APIRouter()


@router.get("/module/{module_id}", response_model=list[LessonRead])
async def list_lessons(module_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.position)
    )
    return result.scalars().all()


@router.post("/", response_model=LessonRead, status_code=201)
async def create_lesson(
    payload: LessonCreate,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    lesson = Lesson(**payload.model_dump())
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    return lesson


@router.patch("/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: UUID,
    payload: LessonUpdate,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    await db.flush()
    await db.refresh(lesson)
    return lesson


@router.put("/{lesson_id}/progress", response_model=LessonProgressRead)
async def update_lesson_progress(
    lesson_id: UUID,
    payload: LessonProgressUpdate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    res = await db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    )
    lp = res.scalar_one_or_none()
    if lp:
        lp.completed = payload.completed
        lp.last_position_seconds = payload.last_position_seconds
        if payload.completed and not lp.completed_at:
            lp.completed_at = datetime.now(timezone.utc)
    else:
        lp = LessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            completed=payload.completed,
            last_position_seconds=payload.last_position_seconds,
            completed_at=datetime.now(timezone.utc) if payload.completed else None,
        )
        db.add(lp)

    await db.flush()

    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if lesson:
        module = await db.get(Module, lesson.module_id)
        if module:
            await recalculate_course_progress(db, user.id, module.course_id)

    if payload.completed and not (lp.completed_at and lp.completed):
        await log_activity(
            db, user.id,
            type=ActivityType.lesson_completed,
            title=f'Completed lesson: "{lesson.title}"' if lesson else "Completed a lesson",
            xp_earned=10,
            metadata={"lesson_id": str(lesson_id)},
        )

    await db.refresh(lp)
    return lp
