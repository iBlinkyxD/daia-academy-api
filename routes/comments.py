from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.comment import Comment
from schemas.comment import CommentCreate, CommentRead
from utils.auth import get_current_user_id
from routes.activities import log_activity
from models.activity import ActivityType

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
    await log_activity(
        db, user.id,
        type=ActivityType.post_commented,
        title="Commented on a post",
        description=comment.content[:120] if comment.content else None,
        metadata={"post_id": str(payload.post_id), "comment_id": str(comment.id)},
    )
    return CommentRead(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author_daia_user_id=daia_user_id,
        author_name=f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
        author_avatar=user.profile_picture_url,
        parent_id=comment.parent_id,
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/post/{post_id}", response_model=list[CommentRead])
async def list_post_comments(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    )
    enriched = []
    for row in result.all():
        c, u = row.Comment, row.User
        enriched.append(CommentRead(
            id=c.id,
            post_id=c.post_id,
            author_id=c.author_id,
            author_daia_user_id=u.daia_user_id,
            author_name=f"{u.first_name or ''} {u.last_name or ''}".strip() or None,
            author_avatar=u.profile_picture_url,
            parent_id=c.parent_id,
            content=c.content,
            created_at=c.created_at,
        ))
    return enriched


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
