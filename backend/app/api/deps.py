"""FastAPI dependency injection."""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.connectors.factory import get_connector
from backend.app.db.engine import AsyncSessionLocal
from backend.app.db.repositories.approval_repository import ApprovalRepository
from backend.app.db.repositories.user_repository import UserRepository
from backend.app.models.auth import SAPRole
from backend.app.schemas.auth import CurrentUser
from backend.app.services.action_planner import ActionPlanner
from backend.app.services.ai_service import AIService
from backend.app.services.approval_facade import ApprovalFacade
from backend.app.services.approval_service import ApprovalService
from backend.app.services.approval_service_db import ApprovalServiceDB
from backend.app.services.auth_service import decode_token
from backend.app.services.context_service import ContextService
from backend.app.services.diagnostic_service import DiagnosticService
from backend.app.services.execution_service import ExecutionService
from backend.app.services.impact_simulator import ImpactSimulator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Singletons ────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _ai_service() -> AIService | None:
    try:
        return AIService()
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_context_service() -> ContextService:
    return ContextService(get_connector())


@lru_cache(maxsize=1)
def get_diagnostic_service() -> DiagnosticService:
    return DiagnosticService(ai_service=_ai_service())


@lru_cache(maxsize=1)
def get_action_planner() -> ActionPlanner:
    return ActionPlanner()


@lru_cache(maxsize=1)
def get_simulator() -> ImpactSimulator:
    return ImpactSimulator()


@lru_cache(maxsize=1)
def get_approval_service() -> ApprovalService:
    return ApprovalService()


@lru_cache(maxsize=1)
def get_execution_service() -> ExecutionService:
    return ExecutionService(get_connector())


# ── Database session ──────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """Yields an AsyncSession when DATABASE_URL is set, else None."""
    if AsyncSessionLocal is None:
        yield None
        return
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Repository dependencies ───────────────────────────────────────────────────


async def get_user_repo(
    db: AsyncSession | None = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


async def get_approval_facade(
    db: AsyncSession | None = Depends(get_db),
) -> ApprovalFacade:
    repo = ApprovalRepository(db) if db is not None else None
    db_svc = ApprovalServiceDB(repo) if repo is not None else None
    return ApprovalFacade(db_svc=db_svc, mem_svc=get_approval_service())


# ── Auth dependencies ─────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession | None = Depends(get_db),
) -> CurrentUser:
    """Decode the JWT and return the calling user.

    This function is overridden in tests via app.dependency_overrides.
    """
    payload = decode_token(token)
    if payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user.id,
        email=user.email,
        role=SAPRole(user.role),
        is_active=user.is_active,
    )


# Role hierarchy — higher value = more privilege
_ROLE_LEVEL: dict[SAPRole, int] = {
    SAPRole.SERVICE: 1,
    SAPRole.CONSULTANT: 2,
    SAPRole.MANAGER: 3,
    SAPRole.ADMIN: 4,
}


def require_role(*roles: SAPRole) -> Callable[..., CurrentUser]:
    """Return a FastAPI dependency that enforces one of the given roles.

    Uses hierarchy: a user passes if their level is >= the minimum level
    in the allowed set.  ADMIN (level 4) passes any gate; MANAGER passes
    CONSULTANT or MANAGER gates; etc.
    """
    min_level = min(_ROLE_LEVEL[r] for r in roles)

    async def _dep(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        user_level = _ROLE_LEVEL.get(current_user.role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.value}' is not authorized. "
                    f"Allowed: {[r.value for r in roles]}"
                ),
            )
        return current_user

    return _dep  # type: ignore[return-value]
