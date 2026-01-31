"""SSE message handler."""

from pydantic import ValidationError
from loguru import logger
from .connection_manager import ConnectionManager
from ..models.message import SSEMessage


class SSEHandler:
    """Handles SSE messages and routes them to WebSocket connections."""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def process_sse_message(self, raw_message: dict) -> bool:
        """Process an SSE message from upstream."""
        try:
            # Validate message format
            message = SSEMessage(**raw_message)

            # Extract user_id
            user_id = message.user_id

            # Send to corresponding user
            success = await self.connection_manager.send_to_user(
                user_id,
                message.data
            )

            if not success:
                logger.warning(f"User {user_id} not connected, message dropped")

            return success

        except ValidationError as e:
            logger.error(f"Invalid SSE message format: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing SSE message: {e}")
            return False

    async def process_batch_sse_messages(self, raw_messages: list) -> list:
        """Process multiple SSE messages."""
        results = []
        for raw_message in raw_messages:
            success = await self.process_sse_message(raw_message)
            results.append({
                "user_id": raw_message.get("user_id"),
                "success": success
            })
        return results
