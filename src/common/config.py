import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


pydantic.BaseSettings = BaseSettings  # чтобы settings прокинуть в config DI


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppSettings(EnvSettings):
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOWED_ORIGINS = ["http://localhost:8080", "http://127.0.0.1:8080"]
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]


class KafkaSettings(EnvSettings):
    KAFKA_URL: str


class AuthSettings(EnvSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int


class DatabaseSettings(EnvSettings):
    """Настройки БД."""

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    @property
    def url(self) -> str:
        """Возвращает урл."""
        return (
            f"postgresql+asyncpg:"
            f"//{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# class CelerySettings(EnvSettings):
#     """Настройки Celery."""
#
#     CELERY_USER: str
#     CELERY_PASSWORD: str
#     CELERY_HOST: str
#     CELERY_PORT: int
#
#     @property
#     def url(self) -> str:
#         """Возвращает урл."""
#         return (
#             f"amqp://{self.CELERY_USER}:{self.CELERY_PASSWORD}"
#             f"@{self.CELERY_HOST}:{self.CELERY_PORT}"
#         )


class RabbitSettings(EnvSettings):
    """Настройки Rabbit."""

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int

    @property
    def url(self) -> str:
        """Возвращает урл."""
        return (
            f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}"
            f"@{self.RABBIT_HOST}:{self.RABBIT_PORT}"
        )


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    kafka: KafkaSettings = KafkaSettings()
    auth: AuthSettings = AuthSettings()
    rabbit: RabbitSettings = RabbitSettings()


settings = Settings()
