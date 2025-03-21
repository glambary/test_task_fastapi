import time


def process_new_order(order_id: int) -> None:
    time.sleep(2)
    print(f"Order {order_id} processed")


CELERY_TASKS = [
    process_new_order,
]
