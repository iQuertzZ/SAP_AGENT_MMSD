from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.app.models.auth import SAPRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    exp: int
    type: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: SAPRole

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: SAPRole
    is_active: bool
    last_login: datetime | None = None


class CurrentUser(BaseModel):
    user_id: str
    email: str
    role: SAPRole
    is_active: bool


class RefreshRequest(BaseModel):
    refresh_token: str
