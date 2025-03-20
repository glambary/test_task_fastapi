from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class OrderBroker(BaseModel):
    id: UUID


class OrderStatusEnum(StrEnum):
    """Статусы заказа."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
