"""SSE event models for WebSocket SSE Server."""

from pydantic import BaseModel, Field
from typing import Optional


class SSEEvent(BaseModel):
    """SSE event model for server-sent events."""

    event: Optional[str] = Field(None, description="Event type")
    data: Optional[str] = Field(None, description="Event data")
    id: Optional[str] = Field(None, description="Event ID")
    retry: Optional[int] = Field(None, description="Retry delay in milliseconds")
