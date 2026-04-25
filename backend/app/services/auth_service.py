"""JWT authentication and password hashing service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from backend.app.core.config import settings
from backend.app.db.models.user import UserORM
from backend.app.db.repositories.user_repository import UserRepository
from backend.app.schemas.auth import TokenPayload


# ── Password ────────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token creation ───────────────────────────────────────────────────────────


def create_access_token(user: UserORM) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user: UserORM) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# ── Token decode ─────────────────────────────────────────────────────────────


def decode_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload(**raw)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── Authentication ────────────────────────────────────────────────────────────


async def authenticate_user(
    email: str, password: str, repo: UserRepository
) -> UserORM:
    user = await repo.get_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
