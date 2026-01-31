"""SSE message handler."""

import asyncio
import json
import uuid
from typing import Dict
from pydantic import ValidationError
from loguru import logger
from .connection_manager import ConnectionManager
from ..models.message import SSEMessage


class SSEHandler:
    """Handles SSE messages and routes them to WebSocket connections."""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        # Store queues for request-response flows (by correlation_id)
        self.request_response_queues: Dict[str, asyncio.Queue] = {}
        # Track message correlation IDs
        self.correlation_map: Dict[str, str] = {}

    async def register_request_response(self, correlation_id: str) -> asyncio.Queue:
        """Register a request-response flow and return a queue for the response."""
        queue = asyncio.Queue()
        self.request_response_queues[correlation_id] = queue
        return queue

    async def unregister_request_response(self, correlation_id: str):
        """Unregister a request-response flow."""
        if correlation_id in self.request_response_queues:
            # Put sentinel value to close the response stream
            await self.request_response_queues[correlation_id].put(None)
            del self.request_response_queues[correlation_id]

    async def send_to_sse_client(self, user_id: str, message: dict) -> bool:
        """Send a message to an SSE client (currently only used for request-response flows)."""
        # This method is kept for potential future use or for request-response flows
        # For now, responses are sent through request_response_queues
        return False

    async def send_to_request_response(self, correlation_id: str, response: dict) -> bool:
        """Send a response to a specific request-response flow."""
        if correlation_id in self.request_response_queues:
            try:
                # Convert response to JSON string
                response_str = json.dumps(response)
                await self.request_response_queues[correlation_id].put(response_str)
                return True
            except Exception as e:
                logger.error(f"Error sending to request-response queue {correlation_id}: {e}")
                return False
        return False

    async def process_sse_message(self, raw_message: dict) -> bool:
        """Process an SSE message from upstream."""
        try:
            # Validate message format
            message = SSEMessage(**raw_message)

            # Extract user_id
            user_id = message.user_id

            # Add user_id to the message data to ensure WebSocket clients know which user this is for
            message.data['user_id'] = user_id

            # Add correlation ID if not present
            correlation_id = message.data.get('correlation_id')
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
                message.data['correlation_id'] = correlation_id

            # Store correlation for tracking responses
            self.correlation_map[correlation_id] = user_id

            # Send to WebSocket connection
            ws_success = await self.connection_manager.send_to_user(
                user_id,
                message.data
            )

            # Return True if delivery to WebSocket succeeded
            return ws_success

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

    async def forward_websocket_response_to_sse(self, user_id: str, response_data: dict) -> bool:
        """Forward a WebSocket response back to the SSE client."""
        # If the response contains a correlation_id, try to send to the request-response flow
        correlation_id = response_data.get('correlation_id')
        if correlation_id and correlation_id in self.request_response_queues:
            # Send to the specific request-response flow
            return await self.send_to_request_response(correlation_id, response_data)
        else:
            # If no correlation_id or no matching request, we can't route the response
            # This is expected for non-request-response flows
            return False
