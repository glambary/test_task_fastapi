from typing import Any
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import UUID, MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовая модель."""

    def as_dict(self) -> dict[str, Any]:
        """Возвращает представление в виде словаря."""
        res = self.__dict__
        res.pop("_sa_instance_state", None)
        return res

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    id = sa.Column(  # noqa: A003
        UUID, primary_key=True, index=True, default=uuid4, unique=True
    )
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=sa.func.now(),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        server_default=sa.func.now(),
    )
