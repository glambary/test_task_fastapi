from enum import StrEnum


class OrderStatusEnum(StrEnum):
    """Статусы заказа."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
