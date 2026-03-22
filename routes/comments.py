from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.comment import Comment
from schemas.comment import CommentCreate, CommentRead
from utils.auth import get_current_user_id

router = APIRouter()


@router.post("/", response_model=CommentRead, status_code=201)
async def create_comment(
    payload: CommentCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    comment = Comment(**payload.model_dump(), author_id=user.id)
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    return comment


@router.get("/post/{post_id}", response_model=list[CommentRead])
async def list_post_comments(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.post_id == post_id))
    return result.scalars().all()


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result_u = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result_u.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result_c = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.author_id == user.id)
    )
    comment = result_c.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.delete(comment)
