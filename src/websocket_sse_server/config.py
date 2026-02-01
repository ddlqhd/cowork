"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Set
import os


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
