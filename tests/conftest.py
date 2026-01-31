"""Pytest configuration for WebSocket SSE Server tests."""

import pytest
from fastapi.testclient import TestClient
from websocket_sse_server.main import app, connection_manager, sse_handler


@pytest.fixture(autouse=True)
async def cleanup():
    """Clean up before each test."""
    # Reset connection manager
    await connection_manager.cleanup()
    yield
    # Clean up after test
    await connection_manager.cleanup()


@pytest.fixture
def client():
    """Create a TestClient instance."""
    return TestClient(app)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    from unittest.mock import AsyncMock
    return AsyncMock()
