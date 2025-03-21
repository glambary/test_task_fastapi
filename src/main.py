import asyncio

import uvicorn
import uvloop

from common.bootstrap import create_app


uvloop.install()
app = asyncio.run(create_app())
celery = app.container.celery()

if __name__ == "__main__":
    uvicorn.run(app, port=8000, host="0.0.0.0")  # noqa: S104
