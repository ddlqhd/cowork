"""SSE message handler."""

import asyncio
import json
import re
import time
import uuid
from typing import Dict, Optional, Tuple
from pydantic import ValidationError
from loguru import logger
from .connection_manager import ConnectionManager
from ..models.message import SSEMessage
from ..config import is_public_account, get_public_accounts
from ..utils.logger import contextual_logger


# Default TTL for correlation entries (in seconds)
CORRELATION_TTL_SECONDS = 300  # 5 minutes


class SSEHandler:
    """Handles SSE messages and routes them to WebSocket connections."""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        # Store queues for request-response flows (by correlation_id)
        self.request_response_queues: Dict[str, asyncio.Queue] = {}
        # Track message correlation IDs with timestamps for TTL-based cleanup
        # Format: {correlation_id: (user_id, timestamp)}
        self.correlation_map: Dict[str, Tuple[str, float]] = {}
        # Lock for correlation_map operations
        self._correlation_lock = asyncio.Lock()

    async def _cleanup_expired_correlations(self) -> int:
        """Remove expired correlation entries based on TTL.
        
        Returns:
            Number of entries cleaned up.
        """
        current_time = time.time()
        expired_keys = []
        
        async with self._correlation_lock:
            for correlation_id, (user_id, timestamp) in self.correlation_map.items():
                if current_time - timestamp > CORRELATION_TTL_SECONDS:
                    expired_keys.append(correlation_id)
            
            for key in expired_keys:
                del self.correlation_map[key]
        
        if expired_keys:
            contextual_logger.debug(f"Cleaned up {len(expired_keys)} expired correlation entries")
        
        return len(expired_keys)

    async def _store_correlation(self, correlation_id: str, user_id: str) -> None:
        """Store a correlation entry with timestamp for TTL tracking."""
        async with self._correlation_lock:
            self.correlation_map[correlation_id] = (user_id, time.time())
        
        # Periodically cleanup expired entries (every 100 new entries)
        if len(self.correlation_map) % 100 == 0:
            await self._cleanup_expired_correlations()

    async def _remove_correlation(self, correlation_id: str) -> None:
        """Remove a correlation entry after it's been used."""
        async with self._correlation_lock:
            if correlation_id in self.correlation_map:
                del self.correlation_map[correlation_id]
                contextual_logger.debug("Removed correlation entry", correlation_id=correlation_id)

    def _get_correlation_user(self, correlation_id: str) -> Optional[str]:
        """Get user_id from correlation map (synchronous, for quick lookups)."""
        entry = self.correlation_map.get(correlation_id)
        if entry:
            return entry[0]  # Return user_id
        return None

    async def register_request_response(self, correlation_id: str) -> asyncio.Queue:
        """Register a request-response flow and return a queue for the response."""
        queue = asyncio.Queue()
        self.request_response_queues[correlation_id] = queue
        contextual_logger.info("Registered request-response flow", correlation_id=correlation_id)
        return queue

    async def unregister_request_response(self, correlation_id: str):
        """Unregister a request-response flow."""
        if correlation_id in self.request_response_queues:
            # Put sentinel value to close the response stream
            await self.request_response_queues[correlation_id].put(None)
            del self.request_response_queues[correlation_id]
            contextual_logger.info("Unregistered request-response flow", correlation_id=correlation_id)

    async def send_to_sse_client(self, user_id: str, message: dict) -> bool:
        """Send a message to an SSE client (currently only used for request-response flows)."""
        # This method is kept for potential future use or for request-response flows
        # For now, responses are sent through request_response_queues
        contextual_logger.debug("Sending message to SSE client (placeholder)", user_id=user_id)
        return False

    async def send_to_request_response(self, correlation_id: str, response: dict) -> bool:
        """Send a response to a specific request-response flow."""
        if correlation_id in self.request_response_queues:
            try:
                # Convert response to JSON string
                response_str = json.dumps(response)
                await self.request_response_queues[correlation_id].put(response_str)
                contextual_logger.debug("Sent response to request-response queue", correlation_id=correlation_id)
                return True
            except Exception as e:
                contextual_logger.error(f"Error sending to request-response queue {correlation_id}: {e}",
                                       correlation_id=correlation_id, error=str(e))
                return False
        else:
            contextual_logger.warning("Attempt to send response to non-existent request-response flow",
                                     correlation_id=correlation_id)
        return False

    async def process_sse_message(self, raw_message: dict) -> bool:
        """Process an SSE message from upstream."""
        try:
            # Validate message format
            message = SSEMessage(**raw_message)

            # Extract user_id
            original_user_id = message.user_id

            # Check if the message contains @public_account pattern
            target_user_id, original_sender_info = self._extract_target_and_sender(original_user_id, message.data)

            # Add original sender info to the message data to ensure public accounts know who sent the message
            message.data['original_sender'] = original_sender_info

            # Add user_id to the message data to ensure WebSocket clients know which user this is for
            # This preserves the original behavior while adding the new functionality
            message.data['user_id'] = original_user_id

            # Add correlation ID if not present
            correlation_id = message.data.get('correlation_id')
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
                message.data['correlation_id'] = correlation_id

            # Store correlation for tracking responses (with TTL)
            await self._store_correlation(correlation_id, target_user_id)

            # Log the message routing
            contextual_logger.info("Processing SSE message",
                                  original_user_id=original_user_id,
                                  target_user_id=target_user_id,
                                  correlation_id=correlation_id)

            # Send to WebSocket connection
            ws_success = await self.connection_manager.send_to_user(
                target_user_id,
                message.data
            )

            if ws_success:
                contextual_logger.debug("SSE message delivered successfully",
                                      target_user_id=target_user_id,
                                      correlation_id=correlation_id)
            else:
                contextual_logger.warning("Failed to deliver SSE message",
                                        target_user_id=target_user_id,
                                        correlation_id=correlation_id)

            # Return True if delivery to WebSocket succeeded
            return ws_success

        except ValidationError as e:
            contextual_logger.error(f"Invalid SSE message format: {e}", error=str(e), raw_message=raw_message)
            return False
        except Exception as e:
            contextual_logger.error(f"Error processing SSE message: {e}", error=str(e), raw_message=raw_message)
            return False

    def _extract_target_and_sender(self, original_user_id: str, message_data: dict) -> Tuple[str, dict]:
        """
        Extract target user ID and original sender info from message.

        Checks if the message contains @public_account pattern and updates target accordingly.

        Args:
            original_user_id: The original user ID from the message
            message_data: The message data

        Returns:
            A tuple of (target_user_id, original_sender_info)
        """
        # Prepare original sender info
        original_sender_info = {
            'user_id': original_user_id,
            'timestamp': message_data.get('timestamp')
        }

        # Check if the message data contains text that might have @mentions
        message_text = ""
        if isinstance(message_data.get('message'), str):
            message_text = message_data['message']
        elif isinstance(message_data.get('text'), str):
            message_text = message_data['text']
        elif isinstance(message_data.get('data'), str):
            message_text = message_data['data']
        elif isinstance(message_data, dict):
            # Look for common fields that might contain text
            for field in ['message', 'text', 'content', 'body']:
                if isinstance(message_data.get(field), str):
                    message_text = message_data[field]
                    break

        # Find @mentions in the message text
        if message_text:
            # Regex pattern to match @username (where username is alphanumeric and underscore)
            pattern = r'@([a-zA-Z0-9_]+)'
            matches = re.findall(pattern, message_text)

            # Check if any matched username is a public account
            for matched_account in matches:
                if is_public_account(matched_account):
                    contextual_logger.info(f"Detected @mention of public account '{matched_account}' from user '{original_user_id}'",
                                          matched_account=matched_account,
                                          original_user_id=original_user_id)
                    return matched_account, original_sender_info

        # If no public account mentioned, return original user_id
        contextual_logger.debug("Using original user for message routing",
                               original_user_id=original_user_id)
        return original_user_id, original_sender_info

    async def process_batch_sse_messages(self, raw_messages: list) -> list:
        """Process multiple SSE messages concurrently for better performance."""
        if not raw_messages:
            return []

        # Create tasks for concurrent processing
        async def process_with_index(idx: int, raw_message: dict) -> dict:
            """Process a single message and return result with index."""
            try:
                success = await self.process_sse_message(raw_message)
                return {
                    "index": idx,
                    "user_id": raw_message.get("user_id"),
                    "success": success
                }
            except Exception as e:
                contextual_logger.error(f"Error processing batch message at index {idx}: {e}",
                                       index=idx, error=str(e))
                return {
                    "index": idx,
                    "user_id": raw_message.get("user_id"),
                    "success": False,
                    "error": str(e)
                }

        # Execute all message processing concurrently
        tasks = [
            process_with_index(idx, raw_message)
            for idx, raw_message in enumerate(raw_messages)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any unexpected exceptions from gather
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                contextual_logger.error(f"Unexpected error in batch processing at index {idx}: {result}",
                                       index=idx, error=str(result))
                processed_results.append({
                    "index": idx,
                    "user_id": raw_messages[idx].get("user_id") if idx < len(raw_messages) else None,
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)

        # Sort by index to maintain order
        processed_results.sort(key=lambda x: x["index"])

        contextual_logger.info(f"Batch processing completed: {len(processed_results)} messages",
                              total=len(processed_results),
                              successful=sum(1 for r in processed_results if r.get("success")))

        return processed_results

    async def forward_websocket_response_to_sse(self, user_id: str, response_data: dict) -> bool:
        """Forward a WebSocket response back to the SSE client."""
        # If the response contains a correlation_id, try to send to the request-response flow
        correlation_id = response_data.get('correlation_id')
        if correlation_id and correlation_id in self.request_response_queues:
            # Send to the specific request-response flow
            success = await self.send_to_request_response(correlation_id, response_data)
            contextual_logger.debug("Forwarded WebSocket response to SSE",
                                  user_id=user_id,
                                  correlation_id=correlation_id,
                                  success=success)
            return success
        else:
            # If no correlation_id or no matching request, we can't route the response
            # This is expected for non-request-response flows
            contextual_logger.debug("Skipping response forwarding - no matching correlation ID",
                                  user_id=user_id,
                                  correlation_id=correlation_id)
            return False
