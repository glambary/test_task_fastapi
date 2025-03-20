from typing import Any
from uuid import UUID

from broker.utils import broker_publish
from repositories.repositories import OrderRepository
from schemas.enums.order import OrderStatusEnum
from schemas.order import OrderDbSchema


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
        await broker_publish({"id": order.id}, "new_order")
        return order

    async def get_order(
        self,
        order_id: UUID,
    ) -> OrderDbSchema:
        return await self.repository.get_by("id", order_id)

    async def update_status(
        self,
        order_id: UUID,
        order_status: OrderStatusEnum,
    ) -> OrderDbSchema:
        return await self.repository.update(order_id, {"status": order_status})

    async def get_orders(
        self,
        user_id: UUID,
    ) -> list[OrderDbSchema]:
        return await self.repository.get_orders(user_id=user_id)
