"""Unit tests for SSEHandler."""

import pytest
from unittest.mock import AsyncMock
from websocket_sse_server.core.sse_handler import SSEHandler
from websocket_sse_server.core.connection_manager import ConnectionManager


class TestSSEHandler:
    """Test SSEHandler functionality."""

    @pytest.fixture
    def handler(self):
        """Create an SSEHandler instance for testing."""
        connection_manager = ConnectionManager()
        return SSEHandler(connection_manager)

    @pytest.mark.asyncio
    async def test_process_sse_message_success(self, handler):
        """Test processing a valid SSE message successfully."""
        # Mock connection
        mock_websocket = AsyncMock()
        await handler.connection_manager.connect("user1", mock_websocket)

        message = {
            "user_id": "user1",
            "data": {"text": "Hello"},
            "event_type": "message"
        }

        result = await handler.process_sse_message(message)
        assert result is True
        mock_websocket.send_json.assert_called_once_with({"text": "Hello"})

    @pytest.mark.asyncio
    async def test_process_sse_message_user_not_connected(self, handler):
        """Test processing message when user is not connected."""
        message = {
            "user_id": "user1",
            "data": {"text": "Hello"}
        }

        result = await handler.process_sse_message(message)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_sse_message_invalid_format(self, handler):
        """Test processing message with invalid format."""
        # Missing required fields
        message = {"data": {"text": "Hello"}}

        result = await handler.process_sse_message(message)
        assert result is False

    @pytest.mark.asyncio
    async def test_process_sse_message_with_optional_fields(self, handler):
        """Test processing message with optional fields."""
        mock_websocket = AsyncMock()
        await handler.connection_manager.connect("user1", mock_websocket)

        message = {
            "user_id": "user1",
            "data": {"text": "Hello"},
            "event_type": "message",
            "event_id": "123",
            "timestamp": 1234567890.0
        }

        result = await handler.process_sse_message(message)
        assert result is True
        mock_websocket.send_json.assert_called_once_with({"text": "Hello"})

    @pytest.mark.asyncio
    async def test_process_batch_sse_messages(self, handler):
        """Test processing multiple SSE messages."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()

        await handler.connection_manager.connect("user1", mock_websocket1)
        await handler.connection_manager.connect("user2", mock_websocket2)

        messages = [
            {"user_id": "user1", "data": {"msg": "msg1"}},
            {"user_id": "user2", "data": {"msg": "msg2"}},
            {"user_id": "user3", "data": {"msg": "msg3"}},  # Not connected
        ]

        results = await handler.process_batch_sse_messages(messages)

        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        assert results[2]["success"] is False

    @pytest.mark.asyncio
    async def test_process_sse_message_connection_error(self, handler):
        """Test processing message when connection fails."""
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Connection error")
        await handler.connection_manager.connect("user1", mock_websocket)

        message = {
            "user_id": "user1",
            "data": {"text": "Hello"}
        }

        result = await handler.process_sse_message(message)
        assert result is False
