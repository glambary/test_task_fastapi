from datetime import timedelta

from fastapi import HTTPException
from starlette import status

from common.config import settings
from repositories.repositories import UserRepository
from schemas.user import UserDbSchema, UserRegisterBodySchema
from services.auth import AuthService


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(
        self,
        repository: UserRepository,
        auth: AuthService,
    ):
        self.repository = repository
        self.auth = auth

    async def create_user(
        self,
        user_data: UserRegisterBodySchema,
    ) -> UserDbSchema:
        # TODO
        #  1) В ТЗ условия нет, но нужно проверить что в базе нет такого email или login
        #  если есть, то вернуть ошибку (например 422)
        #  2) В реальном проекте нужно хэшировать (закодировать) пароль
        return await self.repository.add(insert_data=user_data)

    async def get_token(self, email: str, password: str) -> str:
        """Возвращает токен."""
        user: UserDbSchema = await self.repository.get_by("email", email)

        # TODO Проверка, что пользователь существует
        #  Тут нужно раскодировать пароль и сверить
        if not user or user.password != password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Некорректный email или password",
            )

        token_expires = timedelta(minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = self.auth.create_token({"id": str(user.id)}, token_expires)

        return token
