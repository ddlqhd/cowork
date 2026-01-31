"""SSE endpoints for receiving upstream messages and streaming to clients."""

import asyncio
import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from ..core.sse_handler import SSEHandler
from ..models.message import SSEMessage

router = APIRouter()


def get_sse_handler() -> SSEHandler:
    """Get the global SSE handler instance."""
    from ..main import sse_handler
    return sse_handler


@router.post("/sse/send")
async def send_sse_message_with_response(
    message: SSEMessage,
    request: Request,
    sse_handler: SSEHandler = Depends(get_sse_handler)
):
    """Receive an SSE message from upstream and stream the WebSocket response back."""

    # Generate a unique correlation ID if not provided
    correlation_id = message.data.get('correlation_id', str(uuid.uuid4()))
    message.data['correlation_id'] = correlation_id

    # Create a queue for this specific request to collect the response
    response_queue = await sse_handler.register_request_response(correlation_id)

    async def event_generator():
        try:
            # Forward the message to the WebSocket
            success = await sse_handler.process_sse_message(message.model_dump())

            if not success:
                yield f"data: {json.dumps({'error': 'User not connected', 'correlation_id': correlation_id})}\n\n"
                return

            # Wait for the WebSocket response and stream it back
            while True:
                # Check if client is still connected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for response from WebSocket with timeout
                    response = await asyncio.wait_for(response_queue.get(), timeout=30.0)  # 30 second timeout
                    if response is None:  # Sentinel value to close connection
                        break

                    # Format as SSE event and send
                    yield f"data: {response}\n\n"

                    # If this is a final response, end the stream
                    if isinstance(response, str):
                        response_obj = json.loads(response)
                        if response_obj.get('is_final', False):
                            break

                except asyncio.TimeoutError:
                    # Send timeout message and close connection
                    yield f"data: {json.dumps({'error': 'Timeout waiting for response', 'correlation_id': correlation_id})}\n\n"
                    break

        except Exception as e:
            logger.error(f"Error in SSE request-response stream: {e}")
            yield f"data: {json.dumps({'error': str(e), 'correlation_id': correlation_id})}\n\n"
        finally:
            # Clean up the request-response mapping
            await sse_handler.unregister_request_response(correlation_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sse/push")
async def push_sse_message(
    message: SSEMessage,
    sse_handler: SSEHandler = Depends(get_sse_handler)
):
    """Receive a single SSE message from upstream."""
    try:
        success = await sse_handler.process_sse_message(message.model_dump())

        if success:
            return {"status": "success", "message": "Message delivered"}
        else:
            return {"status": "partial", "message": "User not connected"}

    except Exception as e:
        logger.error(f"Error pushing SSE message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sse/push/batch")
async def push_batch_sse_messages(
    messages: List[SSEMessage],
    sse_handler: SSEHandler = Depends(get_sse_handler)
):
    """Receive multiple SSE messages from upstream."""
    try:
        results = await sse_handler.process_batch_sse_messages(
            [msg.model_dump() for msg in messages]
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error pushing batch SSE messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
