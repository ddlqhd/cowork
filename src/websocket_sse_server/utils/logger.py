"""Logging configuration for the WebSocket SSE server."""

import sys
from loguru import logger
from ..config import settings

# Remove default handler
logger.remove()

# Add custom handler
logger.add(
    sys.stdout,
    level=settings.log_level,
    format=settings.log_format,
    colorize=True,
)

# Add file handler for production
if settings.debug:
    logger.add(
        "websocket_sse_server.log",
        level="DEBUG",
        format=settings.log_format,
        rotation="10 MB",
        retention="10 days",
    )

__all__ = ["logger"]
