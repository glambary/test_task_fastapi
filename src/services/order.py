from typing import Any
from uuid import UUID

from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from broker.utils import broker_publish
from repositories.repositories import OrderRepository
from schemas.enums.order import OrderStatusEnum
from schemas.order import OrderDbSchema
from services.utils.cache import redis_cache


class OrderService:
    """Сервис для работы с заказами."""

    def __init__(
        self,
        repository: OrderRepository,
    ):
        self.repository = repository

    async def create_order(
        self,
        # TODO Нужна pydantic schema
        data: dict[str, Any],
    ) -> OrderDbSchema:
        order = await self.repository.add(data)
        # TODO вынести queue в переменные
        await broker_publish({"data": {"id": order.id}}, "new_order")
        return order

    @redis_cache()
    async def get_order(
        self,
        *,
        order_id: UUID,
        user_id: UUID,
    ) -> OrderDbSchema:
        order = await self.repository.get_by("id", order_id)
        if not order:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
            )
        if order.user_id != user_id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
            )
        return order

    @redis_cache(is_update=True, exclude_kwargs=frozenset("order_status"))
    async def update_status(
        self,
        *order_id: UUID,
        user_id: UUID,
        order_status: OrderStatusEnum,
    ) -> OrderDbSchema:
        await self.get_order(order_id=order_id, user_id=user_id)
        updated_order = await self.repository.update(order_id, {"status": order_status})

        return updated_order

    async def get_orders(
        self,
        user_id: UUID,
    ) -> list[OrderDbSchema]:
        return await self.repository.get_orders(user_id=user_id)
