"""WebSocket endpoints."""

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


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for connection"),
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """WebSocket connection endpoint."""
    await websocket.accept()

    try:
        # Establish connection
        await connection_manager.connect(user_id, websocket)
        logger.info(f"User {user_id} connected")

        # Keep connection alive
        while True:
            # Receive heartbeat or client messages
            data = await websocket.receive_text()
            logger.debug(f"Received from {user_id}: {data}")

            # Handle client messages if needed
            # await handle_client_message(user_id, data)

    except DuplicateConnectionError:
        await websocket.close(code=1008, reason="User already connected")
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        await connection_manager.disconnect(user_id)
