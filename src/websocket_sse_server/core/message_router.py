"""Message routing logic for WebSocket SSE Server."""

from typing import Optional
from ..core.connection_manager import ConnectionManager
from ..core.sse_handler import SSEHandler
from ..utils.logger import logger


class MessageRouter:
    """Route messages between SSE and WebSocket connections."""

    def __init__(self, connection_manager: ConnectionManager, sse_handler: SSEHandler):
        self.connection_manager = connection_manager
        self.sse_handler = sse_handler

    async def route_sse_to_websocket(self, user_id: str, message: dict) -> bool:
        """Route SSE message to WebSocket connection."""
        return await self.connection_manager.send_to_user(user_id, message)

    async def route_websocket_to_sse(self, user_id: str, message: dict) -> None:
        """Route WebSocket message to SSE handler (for future bidirectional support)."""
        logger.debug(f"Routing WebSocket message from {user_id}: {message}")
        # Future: Implement bidirectional message handling if needed
        pass

    async def broadcast_to_all(self, message: dict) -> None:
        """Broadcast message to all connected WebSocket clients."""
        await self.connection_manager.broadcast(message)

    def get_stats(self) -> dict:
        """Get routing statistics."""
        return {
            "active_connections": self.connection_manager.get_connection_count()
        }
