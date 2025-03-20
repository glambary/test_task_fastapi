from uuid import UUID

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
