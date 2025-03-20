import hashlib
import socket
from collections.abc import AsyncIterator
from typing import Any

from cache_sdk.key_builder import _Func
from redis.asyncio import Redis, from_url
from starlette.requests import Request
from starlette.responses import Response


async def init_redis_pool(
    host: str, port: int, password: str = ""
) -> AsyncIterator[Redis]:
    kwargs = {}
    if password:
        kwargs["password"] = password
    session = from_url(
        f"redis://{host}",
        port=port,
        socket_timeout=10,
        socket_keepalive=True,
        socket_keepalive_options={
            socket.TCP_KEEPIDLE: 30,
            socket.TCP_KEEPINTVL: 5,
            socket.TCP_KEEPCNT: 5,
        },
        health_check_interval=5,
        protocol=3,
    )
    yield session
    await session.aclose()


def custom_key_builder(
    __function: _Func,
    __namespace: str = "",
    *,
    _request: Request | None = None,
    _response: Response | None = None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """
    Генератор ключей, который подставляет в ключ id пользователя из request.
    """

    if _request and (user_id := getattr(_request.user, "user_id", None)):
        user_data = f"{user_id}:"
    else:
        user_data = ""

    cache_key = hashlib.sha256(
        f"{__function.__module__}:{__function.__name__}:{args}:{kwargs}".encode()
    ).hexdigest()

    return f"{__namespace}:{user_data}{cache_key}"
