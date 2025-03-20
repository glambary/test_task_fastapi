from dependency_injector.wiring import Provide
from fastapi import Depends

from celery import Celery
from common.container import Container
from schemas.enums.order import OrderBroker


def handle_new_order(
    input_schema: OrderBroker,
    celery: Celery = Depends(Provide[Container.celery]),
):
    task = celery.send_task("process_new_order", args=[input_schema.id])
    task.apply_async()


BROKER_HANDLERS = {
    "new_order": handle_new_order,
}
