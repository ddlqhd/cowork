"""Unit tests for ConnectionManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from websocket_sse_server.core.connection_manager import ConnectionManager
from websocket_sse_server.utils.exceptions import DuplicateConnectionError


class TestConnectionManager:
    """Test ConnectionManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_new_user(self, manager):
        """Test connecting a new user."""
        mock_websocket = AsyncMock()
        await manager.connect("user1", mock_websocket)
        assert "user1" in manager.connections
        assert manager.connections["user1"] == mock_websocket

    @pytest.mark.asyncio
    async def test_connect_duplicate_user(self, manager):
        """Test connecting a duplicate user raises error."""
        mock_websocket = AsyncMock()
        await manager.connect("user1", mock_websocket)

        with pytest.raises(DuplicateConnectionError) as exc_info:
            await manager.connect("user1", mock_websocket)
        assert exc_info.value.user_id == "user1"

    @pytest.mark.asyncio
    async def test_disconnect(self, manager):
        """Test disconnecting a user."""
        mock_websocket = AsyncMock()
        await manager.connect("user1", mock_websocket)
        assert "user1" in manager.connections

        await manager.disconnect("user1")
        assert "user1" not in manager.connections

    @pytest.mark.asyncio
    async def test_send_to_user_success(self, manager):
        """Test sending message to connected user."""
        mock_websocket = AsyncMock()
        await manager.connect("user1", mock_websocket)

        message = {"text": "Hello"}
        result = await manager.send_to_user("user1", message)

        assert result is True
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user_not_connected(self, manager):
        """Test sending message to non-existent user."""
        message = {"text": "Hello"}
        result = await manager.send_to_user("user1", message)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_to_user_error(self, manager):
        """Test sending message when connection fails."""
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Connection error")
        await manager.connect("user1", mock_websocket)

        message = {"text": "Hello"}
        result = await manager.send_to_user("user1", message)

        assert result is False
        assert "user1" not in manager.connections

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting message to all users."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()

        await manager.connect("user1", mock_websocket1)
        await manager.connect("user2", mock_websocket2)

        message = {"text": "Broadcast"}
        sent_count = await manager.broadcast(message)

        assert sent_count == 2
        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_get_connection_count(self, manager):
        """Test getting connection count."""
        assert manager.get_connection_count() == 0

        await manager.connect("user1", AsyncMock())
        assert manager.get_connection_count() == 1

        await manager.connect("user2", AsyncMock())
        assert manager.get_connection_count() == 2

        await manager.disconnect("user1")
        assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test cleanup of all connections."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()

        await manager.connect("user1", mock_websocket1)
        await manager.connect("user2", mock_websocket2)

        await manager.cleanup()

        assert manager.get_connection_count() == 0
        mock_websocket1.close.assert_called_once()
        mock_websocket2.close.assert_called_once()
