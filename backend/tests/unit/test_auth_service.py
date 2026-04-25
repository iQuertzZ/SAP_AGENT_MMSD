"""Unit tests for auth_service — pure functions, no DB required."""
from __future__ import annotations

import time

import pytest

from backend.app.db.models.user import UserORM
from backend.app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.fixture()
def dummy_user() -> UserORM:
    return UserORM(
        id="user-uuid-001",
        email="test@example.com",
        hashed_password=hash_password("secret123"),
        role="admin",
        full_name="Test User",
    )


# ── Password hashing ──────────────────────────────────────────────────────────


def test_hash_password_produces_different_hash_each_time() -> None:
    h1 = hash_password("mypassword")
    h2 = hash_password("mypassword")
    assert h1 != h2  # salt is randomised


def test_verify_password_correct() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("wrong-battery", hashed) is False


# ── Access token round-trip ───────────────────────────────────────────────────


def test_create_and_decode_access_token(dummy_user: UserORM) -> None:
    token = create_access_token(dummy_user)
    payload = decode_token(token)

    assert payload.sub == dummy_user.id
    assert payload.email == dummy_user.email
    assert payload.role == dummy_user.role
    assert payload.type == "access"


def test_create_and_decode_refresh_token(dummy_user: UserORM) -> None:
    token = create_refresh_token(dummy_user)
    payload = decode_token(token)

    assert payload.sub == dummy_user.id
    assert payload.type == "refresh"


# ── Expired / invalid tokens ──────────────────────────────────────────────────


def test_decode_invalid_token_raises_401() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.jwt")
    assert exc_info.value.status_code == 401


def test_decode_tampered_token_raises_401(dummy_user: UserORM) -> None:
    from fastapi import HTTPException

    token = create_access_token(dummy_user)
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401


def test_decode_expired_token_raises_401() -> None:
    """Create a token with negative TTL so it's expired immediately."""
    from fastapi import HTTPException
    from jose import jwt

    from backend.app.core.config import settings

    past = int(time.time()) - 3600
    payload = {
        "sub": "user-001",
        "email": "x@x.com",
        "role": "admin",
        "exp": past,
        "type": "access",
    }
    expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token)
    assert exc_info.value.status_code == 401


# ── authenticate_user ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(dummy_user: UserORM) -> None:
    from fastapi import HTTPException
    from unittest.mock import AsyncMock

    from backend.app.db.repositories.user_repository import UserRepository
    from backend.app.services.auth_service import authenticate_user

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = dummy_user

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user("test@example.com", "wrong-password", repo)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_user_unknown_email() -> None:
    from fastapi import HTTPException
    from unittest.mock import AsyncMock

    from backend.app.db.repositories.user_repository import UserRepository
    from backend.app.services.auth_service import authenticate_user

    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user("nobody@example.com", "any", repo)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_inactive_user(dummy_user: UserORM) -> None:
    from fastapi import HTTPException
    from unittest.mock import AsyncMock

    from backend.app.db.repositories.user_repository import UserRepository
    from backend.app.services.auth_service import authenticate_user

    dummy_user.is_active = False
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_email.return_value = dummy_user

    with pytest.raises(HTTPException) as exc_info:
        await authenticate_user("test@example.com", "secret123", repo)
    assert exc_info.value.status_code == 401
