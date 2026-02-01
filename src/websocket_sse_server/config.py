"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False

    # WebSocket
    ws_path: str = "/ws"
    ws_ping_interval: int = 30  # seconds
    ws_ping_timeout: int = 10   # seconds

    # SSE
    sse_path: str = "/sse/push"
    sse_batch_path: str = "/sse/push/batch"

    # Logging
    log_level: str = "INFO"
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

    # Security
    cors_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
