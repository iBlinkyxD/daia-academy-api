from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.badge import Badge
from models.user import User, UserBadge
from schemas.badge import BadgeCreate, BadgeRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/", response_model=list[BadgeRead])
async def list_badges(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Badge))
    return result.scalars().all()


@router.post("/", response_model=BadgeRead, status_code=201)
async def create_badge(
    payload: BadgeCreate,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    badge = Badge(**payload.model_dump())
    db.add(badge)
    await db.flush()
    await db.refresh(badge)
    return badge


@router.get("/mine", response_model=list[BadgeRead])
async def my_badges(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    res = await db.execute(
        select(Badge).join(UserBadge).where(UserBadge.user_id == user.id)
    )
    return res.scalars().all()
