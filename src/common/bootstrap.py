from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from cache_sdk.backends.redis import RedisBackend
from cache_sdk.base import set_config
from cache_sdk.integrations.fastapi.config import FastAPICacheConfig
from cache_sdk.integrations.fastapi.middleware import FastAPICacheMiddleware
from fastapi_sdk.healthchecker.healthchecker import HealthChecker
from fastapi_sdk.healthchecker.healthchecks import HealthChecks
from faststream.kafka import KafkaBroker
from faststream.rabbit.fastapi import RabbitBroker, RabbitRouter
from sso.authentication import TokenAuthBackend
from sso.exception_handler import auth_exception_handler
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from api.routes import api_router
from broker.hadlers import BROKER_HANDLERS, handle_new_order
from broker.tasks import ROUTES
from celery.tasks import CELERY_TASKS
from common.application import App
from common.config import settings
from common.container import Container
from common.middleware.compression import CompressionMiddleware
from common.redis import custom_key_builder
from exceptions.exception_handler_mapping import (
    updated_exception_handler_mapping,
)


@asynccontextmanager
async def lifespan(app: App) -> AsyncIterator[None]:
    app.logger.info("The app is on")
    yield
    app.logger.info("The app is off")


async def init_container() -> Container:
    """Инициализация контейнера DI."""
    router = RabbitRouter(
        url=settings.rabbit.url,
        lifespan=lifespan,
    )
    # по дефолту брокер создается с apply_types=False
    router.broker = RabbitBroker(settings.rabbit.url)

    container = Container(rabbit_router=router, rabbit_broker=router.broker)

    if resources := container.core.init_resources():
        await resources

    container.check_dependencies()

    return container


def init_sentry() -> None:
    sentry_sdk.init(
        dsn=settings.sentry.SENTRY_DSN,
        environment=settings.app.ENVIRONMENT,
        release=settings.app.RELEASE,
        debug=settings.sentry.SENTRY_DEBUG,
        enable_tracing=True,
        traces_sample_rate=0.2,
        max_request_body_size=settings.sentry.SENTRY_REQUEST_BODIES,
    )


async def create_app() -> App:
    """Формирование app для запуска."""
    container = await init_container()

    # Celery
    celery = container.celery()
    # Регистрация задач Celery
    for t in CELERY_TASKS:
        celery.task(t)

    # Rabbit
    rabbit_broker = container.rabbit_broker()
    # Регистрация обработчиков Rabbit
    for queue, func in BROKER_HANDLERS.items():
        rabbit_broker.subscribe(handle_new_order, queue)

    app = App(
        service_code=settings.app.SERVICE_CODE,
        title=settings.app.PROJECT_NAME,
        exception_handlers=updated_exception_handler_mapping,
        lifespan=kafka_router.lifespan_context,
        jaeger_endpoint=settings.jaeger.JAEGER_ENDPOINT,
        jaeger_mode=settings.jaeger.JAEGER_MODE,
        swagger_ui_parameters={"docExpansion": "none"},
    )
    app.container = container
    app.kafka_broker = kafka_router.broker
    app.kafka_router = kafka_router
    app.logger = structlog.get_logger()

    config = FastAPICacheConfig(
        backend=RedisBackend(
            redis=await container.core.redis_pool(),
            lock_blocking_time=1.0,
        ),
        prefix="bff",
        expire=settings.redis.REDIS_EXPIRE,
        key_builder=custom_key_builder,
        headers_for_cache_key=["Authorization", "X-City", "PLATFORM"],
    )
    set_config(config=config)
    app.add_middleware(
        FastAPICacheMiddleware,
        cached_endpoints=frozenset(),
        cached_routes=frozenset(
            (
                "/api/v1/routers",
                "/api/v2/routers",
            )
        ),
        exclude_endpoints=frozenset(),
        exclude_routes=frozenset(("/api/v1/routers/profile",)),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=settings.app.CORS_ALLOW_CREDENTIALS,
        allow_origins=settings.app.CORS_ALLOW_ORIGINS,
        allow_methods=settings.app.CORS_ALLOW_METHODS,
        allow_headers=settings.app.CORS_ALLOW_HEADERS,
        allow_origin_regex=settings.app.CORS_ALLOW_ORIGIN_REGEX,
    )

    HealthChecker(app=app, healthchecks=HealthChecks())

    app.include_router(kafka_router)
    app.include_router(api_router)
    load_handlers(app.kafka_broker)

    return app


def load_handlers(router: KafkaBroker) -> None:
    """Загрузка обработчиком в зависимости от режима работы."""
    for topic, func in ROUTES.items():
        router.subscriber(topic)(func)
