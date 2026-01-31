"""Pydantic models for message validation."""

from pydantic import BaseModel, Field
from typing import Any, Optional


class SSEMessage(BaseModel):
    """SSE message model for upstream push."""

    user_id: str = Field(..., description="Target user ID")
    data: dict = Field(..., description="Message data payload")
    event_type: Optional[str] = Field(None, description="Event type")
    event_id: Optional[str] = Field(None, description="Event ID")
    timestamp: Optional[float] = Field(None, description="Timestamp")


class ClientMessage(BaseModel):
    """Client message model."""

    type: str = Field(..., description="Message type")
    data: dict = Field(default_factory=dict, description="Message data")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request/response matching")
