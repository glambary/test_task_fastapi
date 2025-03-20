from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from schemas.enums.order import OrderStatusEnum


class OrderDbSchema(BaseModel):
    """Схема заказа."""

    id: UUID
    created_at: datetime
    updated_at: datetime | None
    user_id: UUID
    items: dict[str, Any]
    total_price: float
    status: OrderStatusEnum
