from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing — use bcrypt directly; passlib 1.7.4 is incompatible with bcrypt 4.x
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a signed JWT.

    Args:
        subject: The user's UUID (stored in the ``sub`` claim).
        role: The ``UserRole`` value to embed in the token.
        expires_delta: Override the default expiry from settings.

    Returns:
        A compact, URL-safe JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify *token*.

    Raises:
        jwt.InvalidTokenError: if the token is malformed, expired, or the
            signature does not match.  Callers should map this to a 401.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
