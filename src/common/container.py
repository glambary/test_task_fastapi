"""Контейнер с зависимостями сервиса."""

from dependency_injector import containers, providers

from common.config import Settings
from models.user import User
from repositories.db import Database
from repositories.repositories import UserRepository
from schemas.user import UserDbSchema
from services.auth import AuthService
from services.user import UserService


class Container(containers.DeclarativeContainer):
    """Основной контейнер с зависимостями."""

    __self__ = providers.Self()

    config = providers.Configuration(pydantic_settings=[Settings()])

    wiring_config = containers.WiringConfiguration(
        modules=[
            # "services.utils.cache",
        ],
        packages=["api.v1.routers", "api.v2.routers"],
    )

    # -------------------------------------------------------------------------

    # кэш

    # redis_pool = providers.Resource(
    #     redis.init_redis_pool,
    #     host=config.redis.REDIS_HOST,
    #     port=config.redis.REDIS_PORT,
    #     password=config.redis.REDIS_PASSWORD,
    # )
    # cache_backend: providers.Provider[RedisBackend] = providers.Singleton(
    #     RedisBackend,
    #     redis=redis_pool,
    #     lock_blocking_time=settings.redis.REDIS_BLOCKING_TIMEOUT,  # seconds
    # )
    # cache_service: providers.Provider[CacheService] = providers.Singleton(
    #     CacheService, cache_backend=cache_backend
    # )

    # -------------------------------------------------------------------------

    # Брокер
    # kafka_router: providers.Provider[KafkaRouter] = providers.Dependency(
    #     instance_of=KafkaRouter
    # )
    # kafka_broker: providers.Provider[KafkaBroker] = providers.Dependency(
    #     instance_of=KafkaBroker
    # )

    # -------------------------------------------------------------------------

    # БД и Репозитории

    db: providers.Provider[Database] = providers.Singleton(
        Database,
        db_url=config.db.url,
    )

    user_repository: providers.Provider[UserRepository] = providers.Singleton(
        UserRepository,
        session_factory=db.provided.session,
        model=User,
        model_schema=UserDbSchema,
    )

    # -------------------------------------------------------------------------

    # Сервисы

    auth_service: providers.Provider[AuthService] = providers.Singleton(AuthService)

    user_service: providers.Provider[UserService] = providers.Factory(
        UserService,
    )
