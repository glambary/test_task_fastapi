from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitBroker, RabbitRouter
from starlette.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from broker.handlers import BROKER_HANDLERS
from celery_.tasks import CELERY_TASKS
from common.application import App
from common.config import settings
from common.container import Container


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    print("The app is on")
    yield
    print("The app is off")


async def init_container() -> Container:
    """Инициализация контейнера DI."""

    router = RabbitRouter(
        url=settings.rabbit.url,
        lifespan=lifespan,
    )
    router.broker = RabbitBroker(settings.rabbit.url)

    container = Container(rabbit_router=router, rabbit_broker=router.broker)

    if resources := container.init_resources():
        await resources

    container.check_dependencies()

    return container


async def create_app() -> App:
    """Формирование app для запуска."""
    container = await init_container()

    app = App()
    app.container = container

    # Celery
    celery = container.celery()
    # Регистрация задач Celery
    for t in CELERY_TASKS:
        celery.task(name=t.__name__)(t)

    # Rabbit
    rabbit_router = container.rabbit_router()
    rabbit_broker = container.rabbit_broker()
    # Регистрация обработчиков Rabbit
    for queue, func in BROKER_HANDLERS.items():
        rabbit_broker.subscriber(queue)(func)

    app.include_router(rabbit_router)
    app.include_router(api_router)

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=settings.app.CORS_ALLOW_CREDENTIALS,
        allow_origins=settings.app.CORS_ALLOW_ORIGINS,
        allow_methods=settings.app.CORS_ALLOW_METHODS,
        allow_headers=settings.app.CORS_ALLOW_HEADERS,
    )

    return app
