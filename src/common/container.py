"""Контейнер с зависимостями сервиса."""

from celery import Celery
from dependency_injector import containers, providers
from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter
from redis.asyncio import Redis

from common.config import Settings, settings
from models.order import Order
from models.user import User
from repositories.db import Database
from repositories.repositories import OrderRepository, UserRepository
from schemas.order import OrderDbSchema
from schemas.user import UserDbSchema
from services.auth import AuthService
from services.order import OrderService
from services.user import UserService


class Container(containers.DeclarativeContainer):
    """Основной контейнер с зависимостями."""

    __self__ = providers.Self()

    config = providers.Configuration(pydantic_settings=[Settings()])

    wiring_config = containers.WiringConfiguration(
        modules=[
            "services.utils.cache",
        ],
        packages=["api", "broker"],
    )

    # -------------------------------------------------------------------------

    # кэш
    redis: providers.Provider[Redis] = providers.Singleton(
        Redis,
        host=config.redis.REDIS_HOST,
        port=config.redis.REDIS_PORT,
        password=config.redis.REDIS_PASSWORD,
    )

    # -------------------------------------------------------------------------

    # Брокер и планировщик

    celery: providers.Provider[Celery] = providers.Singleton(
        Celery,
        broker=settings.rabbit.url,
    )
    rabbit_router: providers.Provider[RabbitRouter] = providers.Dependency(
        instance_of=RabbitRouter,
    )
    rabbit_broker: providers.Provider[RabbitBroker] = providers.Dependency(
        instance_of=RabbitBroker,
    )

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

    order_repository: providers.Provider[UserRepository] = providers.Singleton(
        OrderRepository,
        session_factory=db.provided.session,
        model=Order,
        model_schema=OrderDbSchema,
    )

    # -------------------------------------------------------------------------

    # Сервисы

    auth_service: providers.Provider[AuthService] = providers.Singleton(AuthService)
    user_service: providers.Provider[UserService] = providers.Factory(
        UserService,
        repository=user_repository,
        auth=auth_service,
    )
    order_service: providers.Provider[OrderService] = providers.Factory(
        OrderService,
        repository=order_repository,
    )
