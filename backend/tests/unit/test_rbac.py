"""Unit tests for role-based access control (require_role dependency)."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.app.api.deps import require_role
from backend.app.models.auth import SAPRole
from backend.app.schemas.auth import CurrentUser


def _make_user(role: SAPRole) -> CurrentUser:
    return CurrentUser(
        user_id="test-id",
        email=f"{role.value}@test.local",
        role=role,
        is_active=True,
    )


# ── Role authorisation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_role_exact_match_passes() -> None:
    dep = require_role(SAPRole.MANAGER)
    user = _make_user(SAPRole.MANAGER)
    result = await dep(current_user=user)
    assert result.role == SAPRole.MANAGER


@pytest.mark.asyncio
async def test_require_role_wrong_role_raises_403() -> None:
    dep = require_role(SAPRole.ADMIN)
    user = _make_user(SAPRole.CONSULTANT)
    with pytest.raises(HTTPException) as exc_info:
        await dep(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_multi_role_passes_any() -> None:
    dep = require_role(SAPRole.MANAGER, SAPRole.ADMIN)

    manager = _make_user(SAPRole.MANAGER)
    assert (await dep(current_user=manager)).role == SAPRole.MANAGER

    admin = _make_user(SAPRole.ADMIN)
    assert (await dep(current_user=admin)).role == SAPRole.ADMIN


@pytest.mark.asyncio
async def test_require_role_service_account_restricted() -> None:
    """SERVICE cannot approve — only MANAGER and ADMIN can."""
    dep = require_role(SAPRole.MANAGER, SAPRole.ADMIN)
    user = _make_user(SAPRole.SERVICE)
    with pytest.raises(HTTPException) as exc_info:
        await dep(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_do_all_operations() -> None:
    """ADMIN passes every role gate."""
    admin = _make_user(SAPRole.ADMIN)

    for dep in [
        require_role(SAPRole.CONSULTANT),
        require_role(SAPRole.MANAGER),
        require_role(SAPRole.ADMIN),
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN),
    ]:
        result = await dep(current_user=admin)
        assert result.role == SAPRole.ADMIN


@pytest.mark.asyncio
async def test_consultant_cannot_approve() -> None:
    dep = require_role(SAPRole.MANAGER, SAPRole.ADMIN)
    user = _make_user(SAPRole.CONSULTANT)
    with pytest.raises(HTTPException) as exc_info:
        await dep(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_consultant_can_analyze() -> None:
    dep = require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN, SAPRole.SERVICE)
    user = _make_user(SAPRole.CONSULTANT)
    result = await dep(current_user=user)
    assert result.role == SAPRole.CONSULTANT
