import uuid
import httpx
from fastapi import HTTPException

from config import settings


async def upload_post_file(file_bytes: bytes, filename: str, content_type: str, user_id: str) -> str:
    """Upload a file to the Supabase 'posts' bucket and return its public URL."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Storage not configured")

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
    object_path = f"{user_id}/{uuid.uuid4()}.{ext}"
    upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_POSTS_BUCKET}/{object_path}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            upload_url,
            content=file_bytes,
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": content_type,
            },
        )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"Upload failed: {response.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_POSTS_BUCKET}/{object_path}"
    return public_url