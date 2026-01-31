"""SSE endpoints for receiving upstream messages."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from loguru import logger
from ..core.sse_handler import SSEHandler
from ..models.message import SSEMessage

router = APIRouter()


def get_sse_handler() -> SSEHandler:
    """Get the global SSE handler instance."""
    from ..main import sse_handler
    return sse_handler


@router.post("/sse/push")
async def push_sse_message(
    message: SSEMessage,
    sse_handler: SSEHandler = Depends(get_sse_handler)
):
    """Receive a single SSE message from upstream."""
    try:
        success = await sse_handler.process_sse_message(message.dict())

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
            [msg.dict() for msg in messages]
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Error pushing batch SSE messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
