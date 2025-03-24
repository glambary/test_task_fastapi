from typing import Annotated, Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Body, Depends
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from common.container import Container
from schemas.enums.order import OrderStatusEnum
from schemas.order import OrderBodySchema, OrderDbSchema
from schemas.user import UserDbSchema, UserRegisterBodySchema
from services.order import OrderService
from services.user import UserService
from services.utils.auth import check_auth


router = APIRouter()

UserId = Annotated[UUID, Depends(check_auth)]


@router.post(
    "/register/",
)
@inject
async def register(
    body: UserRegisterBodySchema,
    service: UserService = Depends(Provide[Container.user_service]),
) -> UserDbSchema:
    """Регистрирует пользователя."""
    return await service.create_user(user_data=body)


@router.post(
    "/token/",
)
@inject
async def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserService = Depends(Provide[Container.user_service]),
) -> dict[str, Any]:
    """Возвращает JWT токен."""
    return {
        "access_token": await service.get_token(
            email=form_data.username, password=form_data.password
        ),
        "token_type": "bearer",
    }


@router.post(
    "/orders/",
)
@inject
async def create_order(
    user_id: UserId,
    body: OrderBodySchema,
    service: OrderService = Depends(Provide[Container.order_service]),
) -> OrderDbSchema:
    """Возвращает заказы пользователя."""

    return await service.create_order(
        {
            "user_id": user_id,
            "status": OrderStatusEnum.PENDING,
            **body.model_dump(),
        }
    )


@router.get(
    "/orders/{order_id}",
)
@inject
async def get_order(
    order_id: UUID,
    user_id: UserId,
    service: OrderService = Depends(Provide[Container.order_service]),
) -> OrderDbSchema:
    """Возвращает заказ."""
    return await service.get_order(order_id=order_id, user_id=user_id)


@router.patch(
    "/orders/{order_id}",
)
@inject
async def update_order(
    order_id: UUID,
    status: Annotated[OrderStatusEnum, Body(embed=True)],
    user_id: UserId,
    service: OrderService = Depends(Provide[Container.order_service]),
) -> OrderDbSchema:
    """Обновляет статус заказа."""
    return await service.update_status(order_id, user_id, status)


@router.patch(
    "/orders/user/",
)
@inject
async def get_orders(
    user_id: UserId,
    service: OrderService = Depends(Provide[Container.order_service]),
) -> list[OrderDbSchema]:
    """Возвращает заказы пользователя."""
    # TODO Логичнее чтобы путь маршрута был /orders/user/,
    #  а user_id брать из токена
    #  По хорошему нужна пагинация
    return await service.get_orders(user_id=user_id)
