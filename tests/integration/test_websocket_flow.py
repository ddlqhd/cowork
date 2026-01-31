"""Integration tests for WebSocket flow."""

import pytest
from fastapi.testclient import TestClient
from websocket_sse_server.main import app, connection_manager


class TestWebSocketFlow:
    """Test WebSocket integration flow."""

    @pytest.fixture
    def client(self):
        """Create a TestClient instance."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_websocket_connect_and_disconnect(self, client):
        """Test WebSocket connection and disconnection."""
        with client.websocket_connect("/ws?user_id=test123") as websocket:
            # Verify connection is established
            assert connection_manager.get_connection_count() == 1

            # Send a message
            websocket.send_text("ping")

            # Receive echo (if implemented)
            # data = websocket.receive_text()

        # Verify disconnection
        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_websocket_duplicate_connection(self, client):
        """Test duplicate connection is rejected."""
        with client.websocket_connect("/ws?user_id=test123") as websocket1:
            # Try to connect with same user_id
            with pytest.raises(Exception):
                with client.websocket_connect("/ws?user_id=test123") as websocket2:
                    pass

    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(self, client):
        """Test multiple different user connections."""
        with client.websocket_connect("/ws?user_id=user1") as websocket1:
            with client.websocket_connect("/ws?user_id=user2") as websocket2:
                with client.websocket_connect("/ws?user_id=user3") as websocket3:
                    assert connection_manager.get_connection_count() == 3

    @pytest.mark.asyncio
    async def test_websocket_missing_user_id(self, client):
        """Test connection without user_id parameter."""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws") as websocket:
                pass
