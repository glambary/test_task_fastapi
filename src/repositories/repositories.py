from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Insert, Select, Update, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base
from repositories.db import BaseSession
from schemas.order import OrderDbSchema


ModelDB = TypeVar("ModelDB", bound=Base, covariant=True)
ModelDBRow = TypeVar("ModelDBRow", bound=BaseModel, covariant=True)


class BaseRepository(BaseSession):
    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model: ModelDB,
        model_schema: ModelDBRow,
    ) -> None:
        super().__init__(session_factory)

        self._model = model
        self._model_schema = model_schema

    async def add(
        self,
        insert_data: BaseModel | dict[str, Any],
        session: AsyncSession | None = None,
    ):
        if isinstance(insert_data, BaseModel):
            insert_data = insert_data.model_dump()

        query = self.get_insert_query().values(**insert_data)
        async with self.use_or_create_session(session) as session:
            result = await session.scalar(query)
        return self._get_parsed_object(result)

    async def get_by(
        self, field: str, value: Any, session: AsyncSession | None = None
    ) -> ModelDBRow | None:
        """Получение объекта по соответствию полю."""
        query = self.get_base_query().where(getattr(self._model, field) == value)
        async with self.use_or_create_session(session) as session:
            result = await session.scalar(query)
            if result:
                return self._get_parsed_object(result)
            return None

    async def update(
        self,
        pk: UUID,
        obj_in: BaseModel | dict[str, Any],
        session: AsyncSession | None = None,
    ) -> ModelDBRow | None:
        """Update object by pk."""
        if isinstance(obj_in, BaseModel):
            obj_in = obj_in.model_dump(exclude_unset=True)
        query = self.get_update_query().where(self._model.id == pk).values(**obj_in)
        async with self.use_or_create_session(session) as session:
            result = await session.scalar(query)
            if result:
                return self._get_parsed_object(result)
            return None

    def get_base_query(self) -> Select:
        """Get select query."""
        return select(self._model)

    def get_insert_query(self) -> Insert:
        """Get insert query."""
        return insert(self._model).returning(self._model)

    def get_update_query(self) -> Update:
        """Get update query."""
        return update(self._model).returning(self._model)

    def _get_parsed_object(self, raw_result: Any | None) -> ModelDBRow | None:
        """Convert raw to model schema."""
        if raw_result is None:
            return None
        if isinstance(raw_result, Base):
            raw_result = raw_result.as_dict()
        return self._model_schema.model_validate(raw_result)


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""


class OrderRepository(BaseRepository):
    """Репозиторий для работы с заказами."""

    async def get_orders(
        self, user_id: UUID, session: AsyncSession | None = None
    ) -> list[OrderDbSchema]:
        query = self.get_base_query().where(self._model.user_id == user_id)

        async with self.use_or_create_session(session) as session:
            fetch_results = await session.execute(query)
            results = fetch_results.scalars().all()

            if not results:
                return []

            return [self._get_parsed_object(r) for r in results]
