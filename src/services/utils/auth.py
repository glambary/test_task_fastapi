from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer

from services.auth import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/")


# TODO: Авторизацию лучше сделать через middleware
@inject
def check_auth(
    token: str = Security(oauth2_scheme),
    auth_service: AuthService = Depends(Provide["auth_service"]),
) -> UUID:
    """Проверяет токен и возвращает user_id"""
    payload = auth_service.decode_jwt(token)
    return UUID(payload["id"])
