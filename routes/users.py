from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User, UserInterest
from schemas.user import UserCreate, UserRead, UserInterestCreate, UserInterestRead
from utils.auth import get_current_user_id
from config import settings

router = APIRouter()

def verify_internal_secret(x_internal_secret: str = Header(...)):
    """Blocks any call that doesn't come from the DAIA Main API."""
    if x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/register", status_code=201)
async def register_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_internal_secret),
):
    # Prevent duplicate registrations
    result = await db.execute(
        select(User).where(User.daia_user_id == data.daia_user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"message": "User already registered in Academy"}

    user = User(daia_user_id=data.daia_user_id)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "User registered in Academy", "id": str(user.id)}


@router.get("/me", response_model=UserRead)
async def get_me(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/interests", response_model=list[UserInterestRead])
async def get_my_interests(
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    interests = await db.execute(select(UserInterest).where(UserInterest.user_id == user.id))
    return interests.scalars().all()


@router.post("/me/interests", response_model=UserInterestRead, status_code=201)
async def add_interest(
    payload: UserInterestCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    interest = UserInterest(user_id=user.id, interest=payload.interest)
    db.add(interest)
    await db.flush()
    await db.refresh(interest)
    return interest


@router.delete("/me/interests/{interest_id}", status_code=204)
async def delete_interest(
    interest_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    res = await db.execute(
        select(UserInterest).where(UserInterest.id == interest_id, UserInterest.user_id == user.id)
    )
    interest = res.scalar_one_or_none()
    if not interest:
        raise HTTPException(status_code=404, detail="Interest not found")
    await db.delete(interest)
