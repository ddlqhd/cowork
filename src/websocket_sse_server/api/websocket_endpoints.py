"""WebSocket endpoints."""

import json
from fastapi import APIRouter, WebSocket, Query, Depends
from starlette.websockets import WebSocketDisconnect
from loguru import logger
from ..core.connection_manager import ConnectionManager
from ..utils.exceptions import DuplicateConnectionError
from ..core.sse_handler import SSEHandler

router = APIRouter()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    from ..main import connection_manager
    return connection_manager


def get_sse_handler() -> SSEHandler:
    """Get the global SSE handler instance."""
    from ..main import sse_handler
    return sse_handler


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for connection"),
    connection_manager: ConnectionManager = Depends(get_connection_manager),
    sse_handler: SSEHandler = Depends(get_sse_handler)
):
    """WebSocket connection endpoint."""
    await websocket.accept()

    try:
        # Establish connection
        await connection_manager.connect(user_id, websocket)
        logger.info(f"User {user_id} connected")

        # Keep connection alive
        while True:
            try:
                # Receive heartbeat or client messages
                data = await websocket.receive_text()
                logger.debug(f"Received from {user_id}: {data}")

                try:
                    # Parse the received message
                    message_data = json.loads(data)

                    # Use the user_id from the connection for routing the response
                    # but preserve any correlation_id in the message for request-response matching
                    await sse_handler.forward_websocket_response_to_sse(user_id, message_data)

                    # If the message indicates a final response, we could handle special cases here
                    # For example, if the client sends a message indicating the conversation is complete
                    if message_data.get('type') == 'final_response':
                        # Optionally mark this as the final message in the stream
                        final_msg = {**message_data, 'is_final': True}
                        await sse_handler.forward_websocket_response_to_sse(user_id, final_msg)

                    # Optionally, also broadcast to other WebSocket connections if needed
                    # await connection_manager.broadcast(message_data)

                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    response_data = {"message": data, "type": "response", "timestamp": __import__('time').time()}
                    await sse_handler.forward_websocket_response_to_sse(user_id, response_data)
                except Exception as e:
                    logger.error(f"Error processing WebSocket message from {user_id}: {e}")
                    # Send error message back to client
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Error processing your message",
                            "timestamp": __import__('time').time()
                        })
                    except Exception:
                        # If we can't send error message, continue with the loop
                        pass

            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected gracefully")
                break
            except Exception as e:
                logger.error(f"Unexpected error receiving message from {user_id}: {e}")
                break

    except DuplicateConnectionError:
        logger.warning(f"Attempt to connect duplicate user {user_id}")
        await websocket.close(code=1008, reason="User already connected")
        return
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"Critical WebSocket error for user {user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Ignore errors during error handling
    finally:
        await connection_manager.disconnect(user_id)
        logger.info(f"Cleaned up connection for user {user_id}")
