import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from schemas.enums.order import OrderStatusEnum


class Order(Base):
    """Таблица пользователей."""

    __tablename__ = "order"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    items: Mapped[dict[str, Any]] = mapped_column(JSONB())
    total_price: Mapped[float] = mapped_column(Float())
    status: Mapped[OrderStatusEnum] = mapped_column(String(30))
