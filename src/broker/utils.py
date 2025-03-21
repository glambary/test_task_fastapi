from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from faststream.rabbit import RabbitBroker
from faststream.types import SendableMessage


@inject
async def broker_publish(
    message: SendableMessage,
    queue: str,
    broker: RabbitBroker = Depends(Provide["rabbit_broker"]),
) -> None:
    return await broker.publish(
        message=message,
        queue=queue,
    )
