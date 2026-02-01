"""Logging configuration for the WebSocket SSE server."""

import sys
from loguru import logger
from ..config import settings

# Remove default handler
logger.remove()

# Add custom handler with structured logging
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[user_id]} | {message}",
    colorize=True,
    diagnose=True,  # Show variable values in tracebacks
    backtrace=True, # Enable full stack trace
)

# Add file handler for production with structured format
if settings.debug:
    logger.add(
        "websocket_sse_server.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[user_id]} | {extra[endpoint]} | {message}",
        rotation="10 MB",
        retention="10 days",
        serialize=False,  # Keep human-readable format
    )

# Create a contextual logger that can include request-specific information
class ContextualLogger:
    def __init__(self):
        self.logger = logger

    def bind(self, **kwargs):
        """Bind context to logger"""
        return self.logger.bind(**kwargs)

    def info(self, message, **kwargs):
        # Ensure user_id exists in kwargs to prevent KeyError
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 'SYSTEM'
        return self.logger.bind(**kwargs).info(message)

    def error(self, message, **kwargs):
        # Ensure user_id exists in kwargs to prevent KeyError
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 'SYSTEM'
        return self.logger.bind(**kwargs).error(message)

    def warning(self, message, **kwargs):
        # Ensure user_id exists in kwargs to prevent KeyError
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 'SYSTEM'
        return self.logger.bind(**kwargs).warning(message)

    def debug(self, message, **kwargs):
        # Ensure user_id exists in kwargs to prevent KeyError
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 'SYSTEM'
        return self.logger.bind(**kwargs).debug(message)

    def critical(self, message, **kwargs):
        # Ensure user_id exists in kwargs to prevent KeyError
        if 'user_id' not in kwargs:
            kwargs['user_id'] = 'SYSTEM'
        return self.logger.bind(**kwargs).critical(message)

# Create contextual logger instance
contextual_logger = ContextualLogger()

__all__ = ["logger", "contextual_logger"]
