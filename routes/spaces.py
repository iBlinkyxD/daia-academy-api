from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.space import Space, UserSpace, SpaceMemberRole
from schemas.space import SpaceCreate, SpaceRead, UserSpaceRead
from utils.auth import get_current_user_id

router = APIRouter()


async def _resolve_user(daia_user_id: UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=list[SpaceRead])
async def list_spaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Space))
    return result.scalars().all()


@router.post("/", response_model=SpaceRead, status_code=201)
async def create_space(
    payload: SpaceCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    space = Space(**payload.model_dump(), created_by=user.id)
    db.add(space)
    await db.flush()
    db.add(UserSpace(user_id=user.id, space_id=space.id, role=SpaceMemberRole.admin))
    await db.refresh(space)
    return space


@router.post("/{space_id}/join", response_model=UserSpaceRead, status_code=201)
async def join_space(
    space_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    membership = UserSpace(user_id=user.id, space_id=space_id)
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return membership


@router.delete("/{space_id}/leave", status_code=204)
async def leave_space(
    space_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    result = await db.execute(
        select(UserSpace).where(UserSpace.user_id == user.id, UserSpace.space_id == space_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Not a member")
    await db.delete(membership)
