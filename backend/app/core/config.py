from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "LinkFlow"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    BASE_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://linkflow:linkflow_password@localhost:5432/linkflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth
    SECRET_KEY: str = "linkflow-dev-secret-key-change-in-production-must-be-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_REDIRECT_PER_SEC: int = 100
    RATE_LIMIT_CREATE_PER_MIN: int = 30
    RATE_LIMIT_AUTH_PER_MIN: int = 5

    # Security
    SSRF_CHECK_DNS: bool = False

    # Analytics Stream
    REDIS_STREAM_KEY: str = "clicks:stream"
    REDIS_STREAM_GROUP: str = "linkflow_analytics_workers"
    REDIS_STREAM_CONSUMER: str = "worker_1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
