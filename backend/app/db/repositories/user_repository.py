"""UserRepository — DB-backed with in-memory fallback for non-DB environments."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import UserORM

# ── In-memory fallback store (used when no DB is configured) ──────────────
_MEM_STORE: dict[str, UserORM] = {}


class UserRepository:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session

    # ── write ───────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        role: str,
        full_name: str = "",
    ) -> UserORM:
        user = UserORM(
            id=str(uuid.uuid4()),
            email=email.lower(),
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        if self._session:
            self._session.add(user)
            await self._session.flush()
        else:
            _MEM_STORE[user.id] = user
        return user

    async def update_last_login(self, user_id: str) -> None:
        now = datetime.utcnow()
        if self._session:
            result = await self._session.execute(
                select(UserORM).where(UserORM.id == user_id)
            )
            row = result.scalar_one_or_none()
            if row:
                row.last_login = now
                row.updated_at = now
                await self._session.flush()
        else:
            user = _MEM_STORE.get(user_id)
            if user:
                user.last_login = now
                user.updated_at = now

    async def deactivate(self, user_id: str) -> None:
        if self._session:
            result = await self._session.execute(
                select(UserORM).where(UserORM.id == user_id)
            )
            row = result.scalar_one_or_none()
            if row:
                row.is_active = False
                row.updated_at = datetime.utcnow()
                await self._session.flush()
        else:
            user = _MEM_STORE.get(user_id)
            if user:
                user.is_active = False
                user.updated_at = datetime.utcnow()

    # ── read ────────────────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> UserORM | None:
        if self._session:
            result = await self._session.execute(
                select(UserORM).where(UserORM.email == email.lower())
            )
            return result.scalar_one_or_none()
        return next(
            (u for u in _MEM_STORE.values() if u.email == email.lower()),
            None,
        )

    async def get_by_id(self, user_id: str) -> UserORM | None:
        if self._session:
            result = await self._session.execute(
                select(UserORM).where(UserORM.id == user_id)
            )
            return result.scalar_one_or_none()
        return _MEM_STORE.get(user_id)

    async def list_users(
        self,
        role: str | None = None,
        active_only: bool = True,
    ) -> list[UserORM]:
        if self._session:
            stmt = select(UserORM)
            if active_only:
                stmt = stmt.where(UserORM.is_active.is_(True))
            if role:
                stmt = stmt.where(UserORM.role == role)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        users = list(_MEM_STORE.values())
        if active_only:
            users = [u for u in users if u.is_active]
        if role:
            users = [u for u in users if u.role == role]
        return users
