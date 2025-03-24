import json
from typing import Any, Awaitable, Callable, TypeVar, get_type_hints

from dependency_injector.wiring import Provide
from pydantic import BaseModel
from redis.asyncio import Redis


F = TypeVar("F", bound=Callable[..., Any])
F_AWAITABLE = TypeVar("F_AWAITABLE", bound=Callable[..., Awaitable[Any]])


def redis_cache(
    ttl: int = 300, is_update: bool = False, exclude_kwargs: frozenset = frozenset()
) -> F:
    """Декоратор для кэширования ответа в Redis."""

    def decorator(func: F_AWAITABLE) -> F_AWAITABLE:
        # @wraps(func)  # с wraps не работает инъекция
        # https://github.com/ets-labs/python-dependency-injector/issues/454
        async def wrapper(*args, redis: Redis = Provide["redis"], **kwargs) -> Any:
            ## TODO Переделать на middleware
            kwargs = {k: v for k, v in kwargs.items() if k not in exclude_kwargs}

            cache_key = f"{sorted((kwargs.items()))}"
            cached_data = await redis.get(cache_key)

            if cached_data and not is_update:
                cache = json.loads(cached_data)

                hints = get_type_hints(func)  # Получаем аннотации типов
                return_type = hints.get("return")
                if return_type and isinstance(return_type, BaseModel):
                    return return_type.model_validate(cache)

                return cache

            response = await func(*args, **kwargs)

            await redis.setex(
                cache_key, ttl, json.dumps(response.model_dump(mode="json"))
            )

            return response

        return wrapper

    return decorator
