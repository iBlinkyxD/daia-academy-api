from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import get_db
from models.user import User
from models.notification import Notification
from schemas.notification import NotificationRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=list[NotificationRead])
async def list_notifications(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notifs = await db.execute(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    )
    return notifs.scalars().all()


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .values(is_read=True)
    )


@router.patch("/read-all", status_code=204)
async def mark_all_read(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(
        update(Notification).where(Notification.user_id == user.id).values(is_read=True)
    )
