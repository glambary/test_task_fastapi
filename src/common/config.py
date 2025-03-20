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


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    kafka: KafkaSettings = KafkaSettings()
    auth: AuthSettings = AuthSettings()


settings = Settings()
