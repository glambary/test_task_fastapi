from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegisterBodySchema(BaseModel):
    """Схема для регистрации пользователя."""

    email: EmailStr = Field(max_length=300)
    password: str = Field(max_length=100)


class UserDbSchema(BaseModel):
    """Схема пользователя."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    email: EmailStr
    password: str
