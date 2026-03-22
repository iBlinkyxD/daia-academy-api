from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.module import Module
from schemas.module import ModuleCreate, ModuleRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.get("/course/{course_id}", response_model=list[ModuleRead])
async def list_modules(course_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Module).where(Module.course_id == course_id).order_by(Module.position)
    )
    return result.scalars().all()


@router.post("/", response_model=ModuleRead, status_code=201)
async def create_module(
    payload: ModuleCreate,
    _: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    module = Module(**payload.model_dump())
    db.add(module)
    await db.flush()
    await db.refresh(module)
    return module
