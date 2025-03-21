from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from schemas.enums.order import OrderStatusEnum


class OrderBrokerSchema(BaseModel):
    id: UUID


class OrderDbSchema(BaseModel):
    """Схема заказа."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    items: dict[str, Any]
    total_price: float
    status: OrderStatusEnum


class OrderBodySchema(BaseModel):
    """Схема для создания заказа."""

    items: dict[str, Any]
    total_price: float
