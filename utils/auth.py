"""
JWT authentication dependency.
The DAIA main API issues the token; this service only VALIDATES it.
Accepts token from either:
  - HttpOnly cookie (same-domain / local dev)
  - Authorization: Bearer <token> header (cross-domain production)
"""
from uuid import UUID
from fastapi import Cookie, Header, HTTPException, status
import jwt

from config import settings


def _decode_token(token: str) -> UUID:
    payload = jwt.decode(
        token,
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


def _extract_token(
    access_token: str | None,
    authorization: str | None,
) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return access_token


def get_optional_user_id(
    access_token: str = Cookie(None),
    authorization: str | None = Header(None),
) -> UUID | None:
    token = _extract_token(access_token, authorization)
    if not token:
        return None
    try:
        return _decode_token(token)
    except Exception:
        return None


def get_current_user_id(
    access_token: str = Cookie(None),
    authorization: str | None = Header(None),
) -> UUID:
    token = _extract_token(access_token, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return _decode_token(token)
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