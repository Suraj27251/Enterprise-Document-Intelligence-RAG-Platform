"""Simple token-based RBAC helpers for FastAPI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

security_scheme = HTTPBearer(auto_error=True)


def create_access_token(username: str, role: str, expires_minutes: int = 60) -> str:
    """Issue a signed JWT containing role information."""

    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict[str, str]:
    """Decode and validate bearer JWT."""

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.auth_secret_key,
            algorithms=[settings.auth_algorithm],
        )
    except jwt.InvalidTokenError as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    return {"username": payload.get("sub", "unknown"), "role": payload.get("role", "User")}


def require_roles(*allowed_roles: str):
    """Dependency factory enforcing role membership."""

    def _role_guard(user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _role_guard
