"""Integration tests for SSE flow."""

import pytest
from fastapi.testclient import TestClient
from websocket_sse_server.main import app, connection_manager, sse_handler


class TestSSEFlow:
    """Test SSE integration flow."""

    @pytest.fixture
    def client(self):
        """Create a TestClient instance."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_sse_push_single_message(self, client):
        """Test pushing a single SSE message."""
        # First, establish a WebSocket connection
        with client.websocket_connect("/ws?user_id=test123") as websocket:
            # Push SSE message
            response = client.post(
                "/sse/push",
                json={
                    "user_id": "test123",
                    "data": {"text": "Hello from SSE"}
                }
            )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_sse_push_message_to_disconnected_user(self, client):
        """Test pushing message to non-existent user."""
        response = client.post(
            "/sse/push",
            json={
                "user_id": "nonexistent",
                "data": {"text": "Hello"}
            }
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "partial"

    @pytest.mark.asyncio
    async def test_sse_push_batch_messages(self, client):
        """Test pushing multiple SSE messages."""
        with client.websocket_connect("/ws?user_id=user1") as websocket1:
            with client.websocket_connect("/ws?user_id=user2") as websocket2:
                response = client.post(
                    "/sse/push/batch",
                    json=[
                        {"user_id": "user1", "data": {"msg": "msg1"}},
                        {"user_id": "user2", "data": {"msg": "msg2"}},
                        {"user_id": "user3", "data": {"msg": "msg3"}},
                    ]
                )

                assert response.status_code == 200
                result = response.json()
                assert len(result["results"]) == 3
                assert result["results"][0]["success"] is True
                assert result["results"][1]["success"] is True
                assert result["results"][2]["success"] is False

    @pytest.mark.asyncio
    async def test_sse_push_invalid_message(self, client):
        """Test pushing invalid SSE message."""
        response = client.post(
            "/sse/push",
            json={"data": {"text": "Hello"}}  # Missing user_id
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert "connections" in result

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")

        assert response.status_code == 200
        result = response.json()
        assert "active_connections" in result
        assert result["service"] == "websocket-sse-server"
