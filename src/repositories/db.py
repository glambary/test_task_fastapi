"""Base Session."""

from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import (
    AbstractAsyncContextManager,
    AsyncExitStack,
    asynccontextmanager,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from models.base import Base


class Database:
    """Класс БД."""

    def __init__(
        self,
        db_url: str,
        echo: bool = False,
    ) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=echo,
        )
        self._session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self._engine,
        )

    async def create_database(self) -> None:
        """Создает БД."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(
        self,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Возвращает и обрабатывает сессию."""
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class BaseSession:
    """Базовая реализации сессии."""

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
    ) -> None:
        self.session_factory = session_factory

    def use_or_create_session(  # noqa: D102
        self,
        session: AsyncSession | None,
    ) -> AbstractAsyncContextManager[AsyncSession]:
        return self.context_session(session)

    @asynccontextmanager
    async def context_session(  # noqa: D102
        self, session: AsyncSession | None
    ) -> AsyncIterator[AsyncSession]:
        async with AsyncExitStack() as stack:
            if session is None:
                session = await stack.enter_async_context(self.session_factory())
            yield session
