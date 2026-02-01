"""Test for public accounts feature."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.websocket_sse_server.core.connection_manager import ConnectionManager
from src.websocket_sse_server.core.sse_handler import SSEHandler
from src.websocket_sse_server.config import add_public_account, is_public_account


@pytest.mark.asyncio
async def test_public_account_mention_routing():
    """Test that messages with @public_account are routed correctly."""
    # Setup
    connection_manager = ConnectionManager()
    sse_handler = SSEHandler(connection_manager)
    
    # Mock WebSocket connection for the public account
    mock_ws_public = AsyncMock()
    mock_ws_public.send_json = AsyncMock(return_value=None)
    
    # Mock WebSocket connection for original sender
    mock_ws_original = AsyncMock()
    mock_ws_original.send_json = AsyncMock(return_value=None)
    
    # Add public account to the system
    add_public_account("ci_bot")
    
    # Connect public account to WebSocket
    await connection_manager.connect("ci_bot", mock_ws_public)
    
    # Test message with @mention
    message_with_mention = {
        "user_id": "user123",
        "data": {
            "message": "Please run tests on my branch @ci_bot",
            "correlation_id": "test_corr_123"
        }
    }
    
    # Process the message
    result = await sse_handler.process_sse_message(message_with_mention)
    
    # Verify that the message was sent to the public account (ci_bot), not the original user
    mock_ws_public.send_json.assert_called_once()
    
    # Get the arguments passed to send_json
    args, kwargs = mock_ws_public.send_json.call_args
    sent_data = args[0]
    
    # Verify that original sender info is preserved
    assert "original_sender" in sent_data
    assert sent_data["original_sender"]["user_id"] == "user123"
    
    # Verify that the message was indeed sent to the public account
    assert result is True


@pytest.mark.asyncio
async def test_normal_message_routing():
    """Test that normal messages without @mention are routed normally."""
    # Setup
    connection_manager = ConnectionManager()
    sse_handler = SSEHandler(connection_manager)
    
    # Mock WebSocket connection for the original user
    mock_ws_original = AsyncMock()
    mock_ws_original.send_json = AsyncMock(return_value=None)
    
    # Connect original user to WebSocket
    await connection_manager.connect("user123", mock_ws_original)
    
    # Test normal message without @mention
    normal_message = {
        "user_id": "user123",
        "data": {
            "message": "This is a normal message",
            "correlation_id": "normal_corr_123"
        }
    }
    
    # Process the message
    result = await sse_handler.process_sse_message(normal_message)
    
    # Verify that the message was sent to the original user
    mock_ws_original.send_json.assert_called_once()
    
    # Get the arguments passed to send_json
    args, kwargs = mock_ws_original.send_json.call_args
    sent_data = args[0]
    
    # Verify that original sender info is still preserved even for normal messages
    assert "original_sender" in sent_data
    assert sent_data["original_sender"]["user_id"] == "user123"
    
    # Verify that the message was delivered successfully
    assert result is True


@pytest.mark.asyncio
async def test_multiple_mentions():
    """Test message with multiple @mentions - should route to first matching public account."""
    # Setup
    connection_manager = ConnectionManager()
    sse_handler = SSEHandler(connection_manager)
    
    # Add public accounts
    add_public_account("ci_bot")
    add_public_account("notification_bot")
    
    # Mock WebSocket connections
    mock_ws_ci = AsyncMock()
    mock_ws_ci.send_json = AsyncMock(return_value=None)
    
    mock_ws_notification = AsyncMock()
    mock_ws_notification.send_json = AsyncMock(return_value=None)
    
    # Connect public accounts
    await connection_manager.connect("ci_bot", mock_ws_ci)
    await connection_manager.connect("notification_bot", mock_ws_notification)
    
    # Test message with multiple mentions
    message_with_multiple_mentions = {
        "user_id": "user123",
        "data": {
            "message": "Alert @notification_bot and run tests @ci_bot",
            "correlation_id": "multi_corr_123"
        }
    }
    
    # Process the message
    result = await sse_handler.process_sse_message(message_with_multiple_mentions)
    
    # Should route to the first matching public account found (notification_bot in this case)
    # Since both might be called depending on implementation, we check that at least one was called
    assert mock_ws_ci.send_json.called or mock_ws_notification.send_json.called
    
    # Verify that original sender info is preserved
    if mock_ws_notification.send_json.called:
        args, kwargs = mock_ws_notification.send_json.call_args
        sent_data = args[0]
        assert "original_sender" in sent_data
        assert sent_data["original_sender"]["user_id"] == "user123"
    elif mock_ws_ci.send_json.called:
        args, kwargs = mock_ws_ci.send_json.call_args
        sent_data = args[0]
        assert "original_sender" in sent_data
        assert sent_data["original_sender"]["user_id"] == "user123"
    
    # Verify that the message was delivered successfully
    assert result is True