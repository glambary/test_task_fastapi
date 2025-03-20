import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from broker.tasks import ROUTES
from cache_sdk.backends.redis import RedisBackend
from cache_sdk.base import set_config
from cache_sdk.integrations.fastapi.config import FastAPICacheConfig
from cache_sdk.integrations.fastapi.middleware import FastAPICacheMiddleware
from fastapi_sdk.healthchecker.healthchecker import HealthChecker
from fastapi_sdk.healthchecker.healthchecks import HealthChecks
from faststream.kafka import KafkaBroker
from faststream.kafka.fastapi import KafkaRouter
from sso.authentication import TokenAuthBackend
from sso.exception_handler import auth_exception_handler
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware

from api.routes import api_router
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
    router = KafkaRouter(
        settings.kafka.KAFKA_URL,
        lifespan=lifespan,
        include_in_schema=True,
    )
    # по дефолту брокер создается с apply_types=False
    router.broker = KafkaBroker(settings.kafka.KAFKA_URL)

    container = Container(kafka_router=router, kafka_broker=router.broker)

    # DI не знает еще про отдельный пакет pydantic_settings
    container.config.from_dict(settings.model_dump())
    container.core.config.from_dict(settings.model_dump())
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
    if settings.sentry.SENTRY_DSN:
        init_sentry()
    logging.info("Running worker")
    container = await init_container()
    kafka_router = container.kafka_router()

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

    # компрессия должна быть после кэширования
    app.add_middleware(CompressionMiddleware)

    app.add_middleware(
        AuthenticationMiddleware,
        backend=TokenAuthBackend(
            service=app.container.auth_service(),
            verified_endpoints=(
                "/api/v1/routers/auth/logout",
                "/api/v1/routers/reviews",
                "/api/v1/routers/planning_to_go/change_decision",
                "/api/v1/routers/planning_to_go/invite/encode",
            ),
            verified_routes=(
                "/api/v1/routers/favorite",
                "/api/v1/routers/profile",
                "/api/v1/routers/widget",
                "/api/v1/routers/like",
                "/api/v1/routers/loyalty_teen",
            ),
        ),
        on_error=auth_exception_handler,
    )

    # TODO: настроить CORS на основании заголовка Platform
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
