from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException
from starlette import status

from common.config import settings


class AuthService:
    """Репозиторий."""

    _secret_key = settings.auth.SECRET_KEY
    # Алгоритм можно вынести в переменные
    _algorithm = "HS256"

    @classmethod
    def create_token(cls, data: dict[str, Any], expires_delta: timedelta | None = None):
        """Создает JWT-токен."""
        data["exp"] = datetime.now(tz=UTC) + expires_delta or timedelta(hours=1)
        return jwt.encode(data, cls._secret_key, algorithm=cls._algorithm)

    @classmethod
    def decode_jwt(cls, token: str) -> dict[str, Any]:
        """Декодирует JWT-токен и проверяет срок действия"""
        try:
            return jwt.decode(token, cls._secret_key, algorithms=[cls._algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Срок действия токена истек",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Некорректный токен",
            )
