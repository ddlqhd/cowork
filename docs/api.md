# API Reference

The WebSocket SSE Server provides RESTful endpoints for SSE communication and WebSocket endpoints for real-time bidirectional communication.

## WebSocket Endpoint

### Connect to WebSocket
- **URL**: `ws://<host>:<port>/ws?user_id=<user_id>`
- **Method**: WebSocket
- **Description**: Establishes a WebSocket connection for a specific user
- **Query Parameters**:
  - `user_id` (required): Unique identifier for the user connection
- **Headers**: None required
- **Success Response**: 
  - Code: 101 (Switching Protocols)
  - Content: WebSocket connection established
- **Error Responses**:
  - Code: 1008 (Policy Error) - User already connected
  - Code: 1011 (Internal Error) - Internal server error

### Send Message via WebSocket
- **Description**: Send messages to the server via WebSocket
- **Message Format**:
  ```json
  {
    "type": "response",
    "data": {
      "message": "Hello from WebSocket client",
      "correlation_id": "req_123"
    },
    "correlation_id": "req_123"
  }
  ```
- **Response**: Messages are handled by the server and potentially forwarded to SSE clients

## SSE Endpoints

### Send Message with Response (Request-Response)
- **URL**: `POST /sse/send`
- **Description**: Sends a message to a WebSocket client and streams the response back via SSE. This creates a request-response flow.
- **Headers**:
  - `Content-Type`: `application/json`
- **Request Body**:
  ```json
  {
    "user_id": "test123",
    "data": {
      "message": "Hello from upstream!",
      "type": "request",
      "correlation_id": "req_123"
    },
    "event_type": "message",
    "timestamp": 1704067200
  }
  ```
- **Success Response**:
  - Code: 200
  - Content-Type: `text/event-stream`
  - Content: Stream of WebSocket client responses as SSE events
- **Error Response**:
  - Code: 422 - Invalid message format
  - Code: 500 - Internal server error

### Push Message (One-Way)
- **URL**: `POST /sse/push`
- **Description**: Pushes a message to a WebSocket client without expecting a response. This is for one-way notifications to the client.
- **Headers**:
  - `Content-Type`: `application/json`
- **Request Body**:
  ```json
  {
    "user_id": "test123",
    "data": {
      "message": "Hello from upstream!",
      "type": "notification",
      "correlation_id": "req_123"
    },
    "event_type": "message",
    "timestamp": 1704067200
  }
  ```
- **Success Response**:
  - Code: 200
  - Content: 
    ```json
    {
      "status": "success",
      "message": "Message delivered"
    }
    ```
- **Partial Success Response** (when user not connected):
  - Code: 200
  - Content: 
    ```json
    {
      "status": "partial",
      "message": "User not connected"
    }
    ```
- **Error Response**:
  - Code: 422 - Invalid message format
  - Code: 500 - Internal server error

### Push Batch Messages
- **URL**: `POST /sse/push/batch`
- **Description**: Pushes multiple messages to WebSocket clients in a single request.
- **Headers**:
  - `Content-Type`: `application/json`
- **Request Body**:
  ```json
  [
    {
      "user_id": "user1",
      "data": {"msg": "msg1"},
      "event_type": "message"
    },
    {
      "user_id": "user2", 
      "data": {"msg": "msg2"},
      "event_type": "message"
    }
  ]
  ```
- **Success Response**:
  - Code: 200
  - Content:
    ```json
    {
      "results": [
        {
          "index": 0,
          "user_id": "user1",
          "success": true
        },
        {
          "index": 1,
          "user_id": "user2", 
          "success": false
        }
      ]
    }
    ```
- **Error Response**:
  - Code: 422 - Invalid message format
  - Code: 500 - Internal server error

## Utility Endpoints

### Health Check
- **URL**: `GET /health`
- **Description**: Returns the health status of the server.
- **Success Response**:
  - Code: 200
  - Content:
    ```json
    {
      "status": "healthy",
      "connections": 2,
      "uptime": "running"
    }
    ```

### Metrics
- **URL**: `GET /metrics`
- **Description**: Returns server metrics.
- **Success Response**:
  - Code: 200
  - Content:
    ```json
    {
      "active_connections": 2,
      "service": "websocket-sse-server"
    }
    ```

## Message Format

### SSE Message Schema
```json
{
  "user_id": "string (required)",
  "data": "object (required)",
  "event_type": "string (optional)",
  "event_id": "string (optional)",
  "timestamp": "number (optional)"
}
```

### Data Object Schema
The `data` object can contain arbitrary fields but commonly includes:
- `message` or `text`: The main content
- `type`: Message type (e.g., "request", "response", "notification")
- `correlation_id`: ID to correlate requests and responses
- `original_sender`: Information about the original sender (for @mentions)

## Public Account @Mentions

Messages can include @mentions of public accounts (bots) which will route the message to the public account instead of the original recipient:

```json
{
  "user_id": "user123",
  "data": {
    "message": "Please run tests on my branch @ci_bot",
    "correlation_id": "corr-123"
  }
}
```

In this example, the message would be routed to the `ci_bot` account instead of `user123`.