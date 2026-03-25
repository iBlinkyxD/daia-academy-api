"""
JWT authentication dependency.
The DAIA main API issues the token; this service only VALIDATES it.
No tokens are minted here.
"""
from uuid import UUID
from fastapi import Cookie, HTTPException, status
import jwt

from config import settings


def get_optional_user_id(
    access_token: str = Cookie(None),
) -> UUID | None:
    """Same as get_current_user_id but returns None instead of raising."""
    if not access_token:
        return None
    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        return UUID(str(user_id)) if user_id else None
    except Exception:
        return None


def get_current_user_id(
    access_token: str = Cookie(None),
) -> UUID:
    """
    Reads the JWT from the HttpOnly cookie set by the DAIA Main API.
    Validates it and returns the user's daia_user_id.
    Use as a FastAPI dependency in any protected route.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing sub claim",
            )
        return UUID(str(user_id))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )