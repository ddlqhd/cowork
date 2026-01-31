"""
Example application demonstrating bidirectional communication between SSE and WebSocket.
"""

import asyncio
import json
import websockets
import requests
import time
import threading
import uvicorn
from concurrent.futures import ThreadPoolExecutor
from src.websocket_sse_server.main import app


def run_server():
    """Run the main server."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


def test_bidirectional_communication():
    """Test bidirectional communication between SSE and WebSocket."""
    
    print("Starting bidirectional communication test...")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give the server some time to start
    time.sleep(2)
    
    # Test user ID
    user_id = "test_user_123"
    
    # Step 1: Send an SSE message that should be forwarded to WebSocket
    print(f"\n1. Sending SSE message to user {user_id}")
    
    sse_message = {
        "user_id": user_id,
        "data": {
            "message": "Hello from SSE client",
            "action": "echo_request",
            "correlation_id": "corr_123"
        }
    }
    
    response = requests.post("http://127.0.0.1:8000/sse/push", json=sse_message)
    print(f"   SSE push response: {response.status_code}, {response.json()}")
    
    # Step 2: Connect WebSocket and send a response
    print(f"\n2. Connecting WebSocket for user {user_id}")
    
    async def websocket_client():
        uri = f"ws://127.0.0.1:8000/ws?user_id={user_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                print("   ✓ WebSocket connected")
                
                # Send a response message that should be forwarded back to SSE
                response_message = {
                    "type": "response",
                    "data": {
                        "reply": "Hello from WebSocket client",
                        "original_message": "Hello from SSE client",
                        "correlation_id": "corr_123"
                    },
                    "correlation_id": "corr_123"
                }
                
                print(f"   Sending response from WebSocket: {response_message}")
                await websocket.send(json.dumps(response_message))
                
                # Keep connection alive briefly to allow processing
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"   Error in WebSocket client: {e}")
    
    # Run the WebSocket client
    asyncio.run(websocket_client())
    
    print("\n3. Bidirectional communication test completed!")
    print("\nHow it works:")
    print("   - SSE client sends message -> forwarded to WebSocket")
    print("   - WebSocket receives message -> processes and responds")
    print("   - WebSocket response -> forwarded back to SSE client")
    print("\nNote: In a real-world scenario, you would have an actual SSE client")
    print("listening to the /sse/stream/{user_id} endpoint to receive responses.")


if __name__ == "__main__":
    test_bidirectional_communication()