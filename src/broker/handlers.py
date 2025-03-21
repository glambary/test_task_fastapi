from typing import Any

from dependency_injector.wiring import Provide, inject

from common.container import Container
from schemas.order import OrderBrokerSchema


@inject
async def handle_new_order(
    data: OrderBrokerSchema,
    celery: Any = Provide[Container.celery],
) -> None:
    celery.send_task("process_new_order", args=[data.id])


BROKER_HANDLERS = {
    "new_order": handle_new_order,
}
