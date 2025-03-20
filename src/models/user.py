from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class User(Base):
    """Таблица пользователей."""

    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String(300))
    password: Mapped[str] = mapped_column(String(100))
