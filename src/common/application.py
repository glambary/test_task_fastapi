from fastapi import FastAPI

from common.container import Container


class App(FastAPI):
    container: Container
