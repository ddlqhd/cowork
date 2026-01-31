"""WebSocket connection manager."""

import asyncio
from typing import Dict, Optional
from fastapi import WebSocket
from loguru import logger
from ..utils.exceptions import DuplicateConnectionError


class ConnectionManager:
    """Manages WebSocket connections indexed by user_id."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Establish a WebSocket connection for a user."""
        async with self.lock:
            if user_id in self.connections:
                raise DuplicateConnectionError(user_id)
            self.connections[user_id] = websocket

    async def disconnect(self, user_id: str) -> None:
        """Disconnect a user's WebSocket connection."""
        async with self.lock:
            self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """Send a message to a specific user."""
        async with self.lock:
            websocket = self.connections.get(user_id)
            if not websocket:
                return False

            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                await self.disconnect(user_id)
                return False

    async def broadcast(self, message: dict) -> int:
        """Broadcast a message to all connected users."""
        async with self.lock:
            disconnected = []
            sent_count = 0

            for user_id, websocket in self.connections.items():
                try:
                    await websocket.send_json(message)
                    sent_count += 1
                except Exception:
                    disconnected.append(user_id)

            for user_id in disconnected:
                await self.disconnect(user_id)

            return sent_count

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.connections)

    async def cleanup(self) -> None:
        """Clean up all connections."""
        async with self.lock:
            for user_id, websocket in self.connections.items():
                try:
                    await websocket.close(code=1001, reason="Server shutdown")
                except Exception:
                    pass
            self.connections.clear()
