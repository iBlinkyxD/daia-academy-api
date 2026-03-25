from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime
import uuid

from database import get_db
from models.activity import UserActivity, ActivityType
from models.user import User
from utils.auth import get_current_user_id

router = APIRouter()


async def log_activity(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: ActivityType,
    title: str,
    description: str | None = None,
    xp_earned: int = 0,
    metadata: dict | None = None,
) -> None:
    activity = UserActivity(
        user_id=user_id,
        type=type,
        title=title,
        description=description,
        xp_earned=xp_earned,
        extra=metadata,
    )
    db.add(activity)
    # Note: caller is responsible for committing


@router.get("/me")
async def get_my_activities(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    daia_user_id: uuid.UUID = Depends(get_current_user_id),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        return []
    result = await db.execute(
        select(UserActivity)
        .where(UserActivity.user_id == user.id)
        .order_by(desc(UserActivity.created_at))
        .limit(limit)
    )
    activities = result.scalars().all()
    return [_serialize(a) for a in activities]


@router.get("/user/{daia_user_id}")
async def get_user_activities(
    daia_user_id: uuid.UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.daia_user_id == daia_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return []

    result = await db.execute(
        select(UserActivity)
        .where(UserActivity.user_id == user.id)
        .order_by(desc(UserActivity.created_at))
        .limit(limit)
    )
    activities = result.scalars().all()
    return [_serialize(a) for a in activities]


def _serialize(a: UserActivity) -> dict:
    return {
        "id": str(a.id),
        "type": a.type.value,
        "title": a.title,
        "description": a.description,
        "xp_earned": a.xp_earned,
        "metadata": a.extra,
        "created_at": a.created_at.isoformat(),
    }