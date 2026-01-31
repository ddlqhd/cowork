"""Integration tests for WebSocket and SSE combined functionality."""

import asyncio
import pytest
import requests
import websockets
import time
import subprocess
import sys


class TestWebSocketSSEIntegration:
    """Test the integration between WebSocket and SSE functionality."""

    def test_websocket_sse_full_flow(self):
        """Test the complete flow: WebSocket connect -> SSE push -> WebSocket receive."""
        port = 8089
        server_process = subprocess.Popen([
            sys.executable, "-c",
            f"import uvicorn; from src.websocket_sse_server.main import app; uvicorn.run(app, host='127.0.0.1', port={port}, log_level='error')"
        ])

        try:
            # Wait for server to start
            time.sleep(3)

            # Connect WebSocket client and listen for messages
            async def websocket_task():
                uri = f"ws://127.0.0.1:{port}/ws?user_id=integration_test_user"

                async with websockets.connect(uri) as websocket:
                    # Wait for the SSE message
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    return response

            # Start the SSE API call
            def sse_api_call():
                time.sleep(2)  # Give WebSocket time to connect
                response = requests.post(
                    f"http://127.0.0.1:{port}/sse/push",
                    json={
                        "user_id": "integration_test_user",
                        "data": {
                            "message": "Hello from SSE integration test",
                            "timestamp": time.time()
                        }
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"

            # Run both tasks concurrently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit the SSE API call
                sse_future = executor.submit(sse_api_call)

                # Run the WebSocket task
                ws_result = asyncio.run(websocket_task())

                # Wait for SSE call to complete
                sse_future.result()

            # Verify the received message
            assert "Hello from SSE integration test" in ws_result

        finally:
            # Terminate the server process
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    def test_batch_sse_websocket_flow(self):
        """Test the batch SSE to WebSocket flow."""
        port = 8090
        server_process = subprocess.Popen([
            sys.executable, "-c",
            f"import uvicorn; from src.websocket_sse_server.main import app; uvicorn.run(app, host='127.0.0.1', port={port}, log_level='error')"
        ])

        try:
            # Wait for server to start
            time.sleep(3)

            # Connect WebSocket client for user1
            async def websocket_task():
                uri = f"ws://127.0.0.1:{port}/ws?user_id=batch_test_user1"

                async with websockets.connect(uri) as websocket:
                    # Wait for the batch message
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    return response

            # Start the batch SSE API call
            def batch_sse_api_call():
                time.sleep(2)  # Give WebSocket time to connect
                response = requests.post(
                    f"http://127.0.0.1:{port}/sse/push/batch",
                    json=[
                        {
                            "user_id": "batch_test_user1",
                            "data": {"msg": "Batch message 1"}
                        },
                        {
                            "user_id": "batch_test_user2",  # Not connected
                            "data": {"msg": "Batch message 2"}
                        }
                    ],
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                assert response.status_code == 200
                result = response.json()
                assert len(result["results"]) == 2
                # The first user is connected, so should succeed
                assert result["results"][0]["success"] is True
                # The second user is not connected, so should fail
                assert result["results"][1]["success"] is False

            # Run both tasks
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit the batch SSE API call
                sse_future = executor.submit(batch_sse_api_call)

                # Run the WebSocket task
                ws_result = asyncio.run(websocket_task())

                # Wait for SSE call to complete
                sse_future.result()

            # Verify the received message
            assert "Batch message 1" in ws_result

        finally:
            # Terminate the server process
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    def test_health_and_metrics_endpoints_during_activity(self):
        """Test health and metrics endpoints while WebSocket connections are active."""
        port = 8091
        server_process = subprocess.Popen([
            sys.executable, "-c",
            f"import uvicorn; from src.websocket_sse_server.main import app; uvicorn.run(app, host='127.0.0.1', port={port}, log_level='error')"
        ])

        try:
            # Wait for server to start
            time.sleep(3)

            # Connect WebSocket client
            async def websocket_with_metrics_check():
                uri = f"ws://127.0.0.1:{port}/ws?user_id=metrics_test_user"

                async with websockets.connect(uri) as websocket:
                    # Check metrics - should show 1 active connection
                    metrics_resp = requests.get(f"http://127.0.0.1:{port}/metrics")
                    assert metrics_resp.status_code == 200
                    metrics = metrics_resp.json()
                    assert metrics["active_connections"] >= 1  # At least 1 connection

                    # Check health
                    health_resp = requests.get(f"http://127.0.0.1:{port}/health")
                    assert health_resp.status_code == 200
                    health = health_resp.json()
                    assert health["status"] == "healthy"
                    assert health["connections"] >= 1  # At least 1 connection

                    # Send SSE message to this user
                    sse_resp = requests.post(
                        f"http://127.0.0.1:{port}/sse/push",
                        json={
                            "user_id": "metrics_test_user",
                            "data": {"msg": "Test message for metrics"}
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    assert sse_resp.status_code == 200

                    # Receive the message via WebSocket
                    received_msg = await websocket.recv()
                    assert "Test message for metrics" in received_msg

                    # Check metrics again after message delivery
                    metrics_resp_after = requests.get(f"http://127.0.0.1:{port}/metrics")
                    assert metrics_resp_after.status_code == 200
                    metrics_after = metrics_resp_after.json()
                    assert metrics_after["active_connections"] >= 1  # Still at least 1 connection

            # Run the test
            asyncio.run(websocket_with_metrics_check())

        finally:
            # Terminate the server process
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    def test_sse_to_nonexistent_user(self):
        """Test sending SSE message to a non-existent user."""
        port = 8092
        server_process = subprocess.Popen([
            sys.executable, "-c",
            f"import uvicorn; from src.websocket_sse_server.main import app; uvicorn.run(app, host='127.0.0.1', port={port}, log_level='error')"
        ])

        try:
            # Wait for server to start
            time.sleep(3)

            # Send SSE message to non-existent user
            response = requests.post(
                f"http://127.0.0.1:{port}/sse/push",
                json={
                    "user_id": "nonexistent_user",
                    "data": {"msg": "This should fail gracefully"}
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            assert response.status_code == 200  # Should still return 200
            result = response.json()
            assert result["status"] == "partial"  # But indicate partial success

        finally:
            # Terminate the server process
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()