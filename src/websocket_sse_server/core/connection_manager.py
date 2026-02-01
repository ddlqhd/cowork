"""WebSocket connection manager."""

import asyncio
from typing import Dict, Optional, Set
from fastapi import WebSocket
from loguru import logger
from ..utils.exceptions import DuplicateConnectionError
from ..utils.logger import contextual_logger


class ConnectionManager:
    """Manages WebSocket connections indexed by user_id."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        # Use separate locks for different operations to reduce contention
        self._connect_lock = asyncio.Lock()  # Only for connection operations
        self._access_lock = asyncio.Lock()   # For read/write operations

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Establish a WebSocket connection for a user."""
        async with self._connect_lock:
            if user_id in self.connections:
                raise DuplicateConnectionError(user_id)
            self.connections[user_id] = websocket
            contextual_logger.info("User connected", user_id=user_id)

    async def disconnect(self, user_id: str) -> None:
        """Disconnect a user's WebSocket connection."""
        async with self._access_lock:
            if user_id in self.connections:
                del self.connections[user_id]
                contextual_logger.info("User disconnected", user_id=user_id)
            else:
                contextual_logger.warning("Attempt to disconnect non-existent user", user_id=user_id)

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """Send a message to a specific user."""
        # Get the websocket reference without holding the lock during I/O
        websocket_ref = None
        async with self._access_lock:
            websocket_ref = self.connections.get(user_id)

        if not websocket_ref:
            contextual_logger.warning("Attempt to send message to disconnected user", user_id=user_id)
            return False

        try:
            await websocket_ref.send_json(message)
            contextual_logger.debug("Message sent to user", user_id=user_id, message_type=type(message).__name__)
            return True
        except Exception as e:
            contextual_logger.error(f"Error sending to user {user_id}: {e}", user_id=user_id, error=str(e))
            # Remove the user from connections to prevent further attempts
            async with self._access_lock:
                # Double-check the connection still exists and belongs to this user
                if self.connections.get(user_id) == websocket_ref:
                    del self.connections[user_id]
            return False

    async def broadcast(self, message: dict) -> int:
        """Broadcast a message to all connected users."""
        # Get all websocket references without holding the lock during I/O
        connections_copy = {}
        async with self._access_lock:
            connections_copy = self.connections.copy()

        disconnected: Set[str] = set()
        sent_count = 0

        # Process each connection without holding the lock
        for user_id, websocket in connections_copy.items():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                contextual_logger.error(f"Error broadcasting to user {user_id}: {e}", user_id=user_id, error=str(e))
                disconnected.add(user_id)

        # Remove disconnected users from the main dictionary
        if disconnected:
            async with self._access_lock:
                for user_id in disconnected:
                    # Double-check the connection still exists and is the same object
                    if user_id in self.connections and self.connections[user_id] == connections_copy[user_id]:
                        del self.connections[user_id]

        contextual_logger.info(f"Broadcast completed: {sent_count} sent, {len(disconnected)} failed",
                              sent_count=sent_count, failed_count=len(disconnected))
        return sent_count

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        async def _get_count():
            async with self._access_lock:
                return len(self.connections)
        # Since this is called from sync context, we can't use async
        # So we'll use a simple approach that might be slightly inconsistent
        # but won't block other operations
        count = len(self.connections)
        contextual_logger.debug("Connection count retrieved", count=count)
        return count

    async def cleanup(self) -> None:
        """Clean up all connections."""
        connections_to_close = {}
        async with self._access_lock:
            connections_to_close = self.connections.copy()
            self.connections.clear()

        # Close connections without holding the lock
        closed_count = 0
        for user_id, websocket in connections_to_close.items():
            try:
                await websocket.close(code=1001, reason="Server shutdown")
                closed_count += 1
            except Exception as e:
                contextual_logger.warning(f"Error closing websocket for user {user_id}: {e}",
                                         user_id=user_id, error=str(e))

        contextual_logger.info(f"Cleanup completed: {closed_count} connections closed",
                              closed_count=closed_count)
