"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Set, List
import os
import re
from pydantic import field_validator


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
    cors_origins: str = "http://localhost,http://127.0.0.1,https://localhost,https://127.0.0.1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate host format."""
        if not v or not isinstance(v, str):
            raise ValueError('Host must be a non-empty string')
        # Basic validation for IP address or domain name
        if not re.match(r'^[\w\.\-\*]+$', v):
            raise ValueError(f'Invalid host format: {v}')
        return v

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError(f'Port must be between 1 and 65535, got: {v}')
        return v

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}, got: {v}')
        return v.upper()

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins format."""
        if not v:
            raise ValueError('CORS origins cannot be empty')

        origins = [origin.strip() for origin in v.split(',')]
        for origin in origins:
            if origin != "*" and not cls.is_valid_url(origin):
                raise ValueError(f'Invalid CORS origin format: {origin}')

        return v

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Basic URL validation."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:[a-zA-Z0-9-]+\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}'  # domain (including localhost)
            r'(?::[0-9]+)?$'  # optional port
        )
        return bool(url_pattern.match(url)) or url in ['http://localhost', 'https://localhost', 'http://127.0.0.1', 'https://127.0.0.1']


settings = Settings()


# Public accounts configuration
def load_public_accounts_from_env() -> Set[str]:
    """
    Load public accounts from environment variable.

    Environment variable format: PUBLIC_ACCOUNTS=account1,account2,account3
    """
    env_value = os.getenv("PUBLIC_ACCOUNTS", "")
    if env_value:
        return set(account.strip() for account in env_value.split(",") if account.strip())
    return set()


# Default public accounts - can be overridden by environment variable
DEFAULT_PUBLIC_ACCOUNTS: Set[str] = {
    "ci_bot",
    "email_bot",
    "notification_bot",
    "system_bot"
}

# Public accounts set - combines defaults with environment variables
PUBLIC_ACCOUNTS: Set[str] = DEFAULT_PUBLIC_ACCOUNTS.union(load_public_accounts_from_env())


def is_public_account(account_id: str) -> bool:
    """
    Check if an account is a public account.

    Args:
        account_id: The account ID to check

    Returns:
        True if the account is a public account, False otherwise
    """
    return account_id in PUBLIC_ACCOUNTS


def add_public_account(account_id: str) -> None:
    """
    Add a new public account dynamically.

    Args:
        account_id: The account ID to add
    """
    PUBLIC_ACCOUNTS.add(account_id)


def get_public_accounts() -> Set[str]:
    """
    Get all public accounts.

    Returns:
        Set of public account IDs
    """
    return PUBLIC_ACCOUNTS.copy()
