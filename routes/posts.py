from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.user import User
from models.post import Post, PostLike
from models.comment import Comment
from schemas.post import PostCreate, PostRead, PostUpdate
from utils.auth import get_current_user_id

router = APIRouter()


async def _resolve_user(daia_user_id: UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _enrich(post: Post, user: User) -> PostRead:
    data = PostRead.model_validate(post)
    data.author_daia_user_id = user.daia_user_id
    return data


@router.get("/", response_model=list[PostRead])
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post).order_by(Post.created_at.desc()).offset(offset).limit(limit)
    )
    posts = result.scalars().all()
    # Bulk-load authors
    author_ids = list({p.author_id for p in posts})
    users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}
    return [_enrich(p, users_map[p.author_id]) for p in posts if p.author_id in users_map]


@router.post("/", response_model=PostRead, status_code=201)
async def create_post(
    payload: PostCreate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    post = Post(**payload.model_dump(), author_id=user.id)
    db.add(post)
    await db.flush()
    await db.refresh(post)
    return _enrich(post, user)


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.get("/{post_id}/stats")
async def get_post_stats(post_id: UUID, db: AsyncSession = Depends(get_db)):
    """Computed counts — never stored as columns."""
    likes = await db.execute(select(func.count(PostLike.id)).where(PostLike.post_id == post_id))
    comments = await db.execute(select(func.count(Comment.id)).where(Comment.post_id == post_id))
    return {"post_id": post_id, "likes_count": likes.scalar(), "comments_count": comments.scalar()}


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: UUID,
    payload: PostUpdate,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    result = await db.execute(select(Post).where(Post.id == post_id, Post.author_id == user.id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not yours")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(post, field, value)
    await db.flush()
    await db.refresh(post)
    return post


@router.post("/{post_id}/like", status_code=201)
async def like_post(
    post_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    db.add(PostLike(user_id=user.id, post_id=post_id))
    return {"liked": True}


@router.delete("/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: UUID,
    daia_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _resolve_user(daia_user_id, db)
    result = await db.execute(
        select(PostLike).where(PostLike.user_id == user.id, PostLike.post_id == post_id)
    )
    like = result.scalar_one_or_none()
    if like:
        await db.delete(like)
