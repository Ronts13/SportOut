from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.enums import UserRole
from app.core.security import decode_access_token

# Points to the (future) auth token endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------
class TokenData(BaseModel):
    """Claims extracted from a validated JWT."""

    user_id: str
    role: str


# ---------------------------------------------------------------------------
# Base dependency
# ---------------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Extract and validate the Bearer JWT.

    Raises:
        HTTPException 401: if the token is missing, malformed, expired, or
            missing required claims.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if not user_id or not role:
            raise credentials_exc
    except jwt.InvalidTokenError:
        raise credentials_exc

    return TokenData(user_id=user_id, role=role)


def get_optional_user(request: Request) -> TokenData | None:
    """Like get_current_user but returns None if no token is present.
    Used for endpoints that are public but can be enriched when logged in.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):]
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id and role:
            return TokenData(user_id=user_id, role=role)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Role-scoped dependencies
# ---------------------------------------------------------------------------
def get_current_facility_manager(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Require the caller to hold the FACILITY_MANAGER or ADMIN role.

    Raises:
        HTTPException 403: if the role is insufficient.
    """
    allowed = {UserRole.FACILITY_MANAGER.value, UserRole.ADMIN.value}
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Facility manager access required",
        )
    return current_user


def get_current_admin(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Require the caller to hold the ADMIN role.

    Raises:
        HTTPException 403: if the role is insufficient.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
