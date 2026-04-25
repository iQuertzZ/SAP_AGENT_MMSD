"""
Authentication routes — /api/v1/auth/*

POST /auth/login        — issue access + refresh tokens
POST /auth/refresh      — rotate tokens
POST /auth/logout       — client-side invalidation (stateless)
GET  /auth/me           — current user info
POST /auth/users        — create user (ADMIN)
GET  /auth/users        — list users (ADMIN)
PATCH /auth/users/{id}/deactivate — disable user (ADMIN)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.api.deps import get_current_user, get_user_repo, require_role
from backend.app.db.repositories.user_repository import UserRepository
from backend.app.models.auth import SAPRole
from backend.app.schemas.auth import (
    CurrentUser,
    RefreshRequest,
    Token,
    UserCreate,
    UserResponse,
)
from backend.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_to_response(user) -> UserResponse:  # type: ignore[no-untyped-def]
    return UserResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=SAPRole(user.role),
        is_active=user.is_active,
        last_login=user.last_login,
    )


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repo),
) -> Token:
    user = await authenticate_user(form.username, form.password, repo)
    await repo.update_last_login(user.id)
    return Token(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        expires_in=60 * 60,  # seconds matching ACCESS_TOKEN_EXPIRE_MINUTES default
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    body: RefreshRequest,
    repo: UserRepository = Depends(get_user_repo),
) -> Token:
    payload = decode_token(body.refresh_token)
    if payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh",
        )
    user = await repo.get_by_id(payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return Token(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        expires_in=60 * 60,
    )


@router.post("/logout")
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    # Stateless JWT — invalidation is client-side
    return {"message": "logged out", "user": current_user.email}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repo),
) -> UserResponse:
    user = await repo.get_by_id(current_user.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    repo: UserRepository = Depends(get_user_repo),
    _: CurrentUser = Depends(require_role(SAPRole.ADMIN)),
) -> UserResponse:
    existing = await repo.get_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {body.email!r} already exists",
        )
    user = await repo.create(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role.value,
        full_name=body.full_name,
    )
    return _user_to_response(user)


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: SAPRole | None = None,
    active_only: bool = True,
    repo: UserRepository = Depends(get_user_repo),
    _: CurrentUser = Depends(require_role(SAPRole.ADMIN)),
) -> list[UserResponse]:
    users = await repo.list_users(
        role=role.value if role else None,
        active_only=active_only,
    )
    return [_user_to_response(u) for u in users]


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    repo: UserRepository = Depends(get_user_repo),
    _: CurrentUser = Depends(require_role(SAPRole.ADMIN)),
) -> dict:
    user = await repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await repo.deactivate(user_id)
    return {"message": "user deactivated", "user_id": user_id}
