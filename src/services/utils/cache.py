import json
from typing import Any, Awaitable, Callable, TypeVar

from dependency_injector.wiring import Provide
from fastapi import Depends
from redis import Redis
from starlette.requests import Request


F = TypeVar("F", bound=Callable[..., Any])
F_AWAITABLE = TypeVar("F_AWAITABLE", bound=Callable[..., Awaitable[Any]])


def redis_cache(ttl: int = 300) -> F:
    """Декоратор для кэширования ответа в Redis."""

    def decorator(func: F_AWAITABLE) -> F_AWAITABLE:
        # @wraps(func)  # с wraps не работает инъекция
        # https://github.com/ets-labs/python-dependency-injector/issues/454
        async def wrapper(
            *args, request: Request, redis: Redis = Depends(Provide["redis"]), **kwargs
        ) -> Any:
            # TODO на самом деле нужно учить ещё и хедеры
            #  лучше параметры сортировать
            #  Переделать на middleware
            cache_key = f"{request.url.path}?{request.query_params}"
            cached_data = await redis.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

            response = await func(*args, **kwargs)

            await redis.setex(cache_key, ttl, json.dumps(response))

            return response

        return wrapper

    return decorator
