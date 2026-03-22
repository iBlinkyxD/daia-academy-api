"""
HTTP client for fetching user profile data from the DAIA main API.
Use sparingly — only when a response needs to embed user profile fields
(name, avatar) that are not stored in the Academy DB.
"""
from uuid import UUID
import httpx
from fastapi import HTTPException

from config import settings


async def get_daia_user_profile(daia_user_id: UUID, bearer_token: str) -> dict:
    """Fetch user profile from DAIA API using the caller's token."""
    url = f"{settings.DAIA_API_BASE_URL}/users/{daia_user_id}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found in DAIA API")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="DAIA API unavailable")
    return response.json()


async def get_daia_users_batch(daia_user_ids: list[UUID], bearer_token: str) -> dict[str, dict]:
    """
    Batch-fetch multiple user profiles. Returns a dict keyed by str(user_id).
    Falls back gracefully if some users are missing.
    """
    url = f"{settings.DAIA_API_BASE_URL}/users/batch"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            json={"ids": [str(uid) for uid in daia_user_ids]},
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
    if response.status_code != 200:
        return {}
    return {u["id"]: u for u in response.json()}
