from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.user import User
from models.post import Post, PostLike
from models.comment import Comment
from models.notification import Notification, NotificationType
from schemas.post import PostCreate, PostRead, PostUpdate
from utils.auth import get_current_user_id, get_optional_user_id
from routes.activities import log_activity
from models.activity import ActivityType
from services.storage import upload_post_file

router = APIRouter()


async def _resolve_user(daia_user_id: UUID, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.daia_user_id == daia_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _enrich(
    post: Post,
    user: User,
    likes_count: int = 0,
    comments_count: int = 0,
    liked_by_me: bool = False,
) -> PostRead:
    data = PostRead.model_validate(post)
    data.author_daia_user_id = user.daia_user_id
    data.author_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or None
    data.author_avatar = user.profile_picture_url
    data.likes_count = likes_count
    data.comments_count = comments_count
    data.liked_by_me = liked_by_me
    return data


@router.get("/", response_model=list[PostRead])
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    viewer_daia_id: UUID | None = Depends(get_optional_user_id),
):
    likes_sq = (
        select(func.count(PostLike.id))
        .where(PostLike.post_id == Post.id)
        .correlate(Post)
        .scalar_subquery()
    )
    comments_sq = (
        select(func.count(Comment.id))
        .where(Comment.post_id == Post.id)
        .correlate(Post)
        .scalar_subquery()
    )

    result = await db.execute(
        select(Post, likes_sq.label("likes_count"), comments_sq.label("comments_count"))
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()

    author_ids = list({r.Post.author_id for r in rows})
    users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    users_map = {u.id: u for u in users_result.scalars().all()}

    liked_post_ids: set = set()
    if viewer_daia_id:
        viewer_res = await db.execute(select(User).where(User.daia_user_id == viewer_daia_id))
        viewer = viewer_res.scalar_one_or_none()
        if viewer:
            likes_res = await db.execute(
                select(PostLike.post_id).where(PostLike.user_id == viewer.id)
            )
            liked_post_ids = {r[0] for r in likes_res.all()}

    posts = []
    for row in rows:
        post = row.Post
        if post.author_id not in users_map:
            continue
        posts.append(_enrich(
            post,
            users_map[post.author_id],
            likes_count=row.likes_count or 0,
            comments_count=row.comments_count or 0,
            liked_by_me=post.id in liked_post_ids,
        ))
    return posts


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    daia_user_id: UUID = Depends(get_current_user_id),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    file_bytes = await file.read()
    url = await upload_post_file(
        file_bytes,
        filename=file.filename or "upload",
        content_type=file.content_type,
        user_id=str(daia_user_id),
    )
    return {"url": url}


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    daia_user_id: UUID = Depends(get_current_user_id),
):
    file_bytes = await file.read()
    url = await upload_post_file(
        file_bytes,
        filename=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
        user_id=str(daia_user_id),
    )
    return {"url": url, "name": file.filename}


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
    await log_activity(
        db, user.id,
        type=ActivityType.post_created,
        title="Created a post",
        description=post.content[:120] if post.content else None,
        metadata={"post_id": str(post.id)},
    )
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
    await log_activity(
        db, user.id,
        type=ActivityType.post_liked,
        title="Liked a post",
        metadata={"post_id": str(post_id)},
    )
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalar_one_or_none()
    if post and post.author_id != user.id:
        liker_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Someone"
        db.add(Notification(
            user_id=post.author_id,
            type=NotificationType.post_like,
            title=f"{liker_name} liked your post",
            resource_id=post_id,
            resource_type="post",
        ))
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
