# WebSocket SSE Server

A FastAPI-based server that provides bidirectional communication between Server-Sent Events (SSE) and WebSocket connections.

## Features

- **WebSocket Server**: Handle WebSocket connections with user ID extraction
- **SSE Stream Endpoint**: Real-time SSE stream for receiving messages from server
- **SSE Push Endpoint**: HTTP endpoint for receiving upstream SSE messages
- **Bidirectional Communication**: Forward messages from SSE to WebSocket and responses back to SSE
- **Message Correlation**: Match requests and responses using correlation IDs
- **Message Routing**: Route messages to appropriate WebSocket/SSE connections based on user ID
- **Connection Management**: Thread-safe connection management with proper cleanup
- **Batch Support**: Support for batch message processing
- **Health Checks**: Health and metrics endpoints

## Architecture

```
┌─────────────┐    SSE Messages      ┌─────────────────┐    WebSocket
│ SSE Client  │ ────────────────→    │                 │ ←──────────────  ┌─────────────┐
│             │                      │  FastAPI        │                   │ WebSocket   │
│             │                      │  Server         │                   │ Client      │
└─────────────┘                      │                 │                   └─────────────┘
                                     │ • WebSocket     │
┌─────────────┐    ←──────────────   │ • SSE Handler   │    ←──────────────  ┌─────────────┐
│ SSE Client  │    WebSocket         │ • Connection    │                   │ WebSocket   │
│ (Response)  │    Response          │   Manager       │                   │ (Response)  │
└─────────────┘                      │                 │                   └─────────────┘
```

## Project Structure

```
websocket-sse-server/
├── src/
│   └── websocket_sse_server/
│       ├── __init__.py
│       ├── main.py                    # FastAPI application
│       ├── config.py                  # Configuration (pydantic settings)
│       ├── models/
│       │   ├── __init__.py
│       │   └── message.py            # Pydantic models
│       ├── core/
│       │   ├── __init__.py
│       │   ├── connection_manager.py # WebSocket connection manager
│       │   └── sse_handler.py        # SSE message processor
│       ├── api/
│       │   ├── __init__.py
│       │   ├── websocket_endpoints.py # WebSocket routes
│       │   └── sse_endpoints.py      # SSE endpoints
│       └── utils/
│           ├── __init__.py
│           ├── logger.py             # Logging configuration
│           └── exceptions.py         # Custom exceptions
├── tests/
│   ├── unit/
│   │   ├── test_connection_manager.py
│   │   └── test_sse_handler.py
│   └── integration/
│       ├── test_websocket_flow.py
│       └── test_sse_flow.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Installation

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Using pyproject.toml

```bash
# Install in development mode
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure as needed:

```bash
cp .env.example .env
```

Example `.env`:

```env
HOST=0.0.0.0
PORT=8080
DEBUG=false
WS_PATH=/ws
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10
SSE_PATH=/sse/push
SSE_BATCH_PATH=/sse/push/batch
LOG_LEVEL=INFO
LOG_FORMAT={time:YYYY-MM-DD HH:mm:ss} | {level} | {message}
CORS_ORIGINS=*

# Public accounts configuration
# Comma-separated list of public accounts that can receive messages via @mentions
# Example: PUBLIC_ACCOUNTS=ci_bot,email_bot,notification_bot
PUBLIC_ACCOUNTS=
```

## Running the Server

### Development

```bash
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080 --reload
```

### Production

```bash
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
```

### Using Docker

```bash
docker build -t websocket-sse-server .
docker run -p 8080:8080 websocket-sse-server
```

Or with docker-compose:

```bash
docker-compose up
```

## API Endpoints

### WebSocket Endpoint

**URL**: `ws://localhost:8080/ws?user_id=<user_id>`

**Example**:

```bash
# Using wscat
wscat -c "ws://localhost:8080/ws?user_id=test123"

# Using browser
const ws = new WebSocket('ws://localhost:8080/ws?user_id=test123');
ws.onmessage = (event) => console.log(event.data);
```

### SSE Request-Response Endpoint

**URL**: `POST /sse/send`

**Description**: Sends a message to a WebSocket client and streams the response back via SSE. This creates a request-response flow where the upstream service can receive the WebSocket client's response in real-time.

**Request Body**:

```json
{
  "user_id": "test123",
  "data": {"message": "Hello from upstream!", "type": "request", "correlation_id": "req_123"},
  "event_type": "message",
  "event_id": "123",
  "timestamp": 1704067200
}
```

### Public Accounts Feature

The system supports public accounts (such as CI bots, email bots, etc.) that can receive messages from any user. Users can send messages to public accounts using the @mention syntax in their message content.

**Supported Public Accounts**: By default, the system recognizes the following public accounts:
- `ci_bot`
- `email_bot`
- `notification_bot`
- `system_bot`

You can configure additional public accounts using the `PUBLIC_ACCOUNTS` environment variable.

**Example**: To send a message to the CI bot, include `@ci_bot` in your message:
```json
{
  "user_id": "user123",
  "data": {
    "message": "Please run tests on my branch @ci_bot",
    "correlation_id": "corr-123"
  }
}
```

When a message contains a @mention of a public account, the message will be routed to that public account's WebSocket connection instead of the originally specified user. The public account will receive the message along with the `original_sender` information so it knows who sent the request.

**Environment Configuration**:
To add custom public accounts, set the `PUBLIC_ACCOUNTS` environment variable:
```
PUBLIC_ACCOUNTS=custom_bot1,custom_bot2,another_bot
```

**Example**:

```bash
curl -X POST http://localhost:8080/sse/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test123",
    "data": {"message": "Hello from upstream!", "type": "request", "correlation_id": "req_123"},
    "event_type": "message",
    "timestamp": 1704067200
  }'
```

**Response**: Streams back WebSocket client responses as SSE events until the conversation is complete or timeout occurs.

### SSE Push Endpoint

**URL**: `POST /sse/push`

**Description**: Pushes a message to a WebSocket client without expecting a response. This is for one-way notifications to the client.

**Request Body**:

```json
{
  "user_id": "test123",
  "data": {"message": "Hello from upstream!", "type": "notification", "correlation_id": "req_123"},
  "event_type": "message",
  "event_id": "123",
  "timestamp": 1704067200
}
```

**Example**:

```bash
curl -X POST http://localhost:8080/sse/push \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test123",
    "data": {"message": "Hello from upstream!", "type": "notification", "correlation_id": "req_123"},
    "event_type": "message",
    "timestamp": 1704067200
  }'
```

### SSE Batch Push Endpoint

**URL**: `POST /sse/push/batch`

**Request Body**:

```json
[
  {"user_id": "user1", "data": {"msg": "msg1"}},
  {"user_id": "user2", "data": {"msg": "msg2"}}
]
```

**Example**:

```bash
curl -X POST http://localhost:8080/sse/push/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"user_id": "user1", "data": {"msg": "msg1"}},
    {"user_id": "user2", "data": {"msg": "msg2"}}
  ]'
```

### Health Check

**URL**: `GET /health`

**Example**:

```bash
curl http://localhost:8080/health
```

**Response**:

```json
{
  "status": "healthy",
  "connections": 2,
  "uptime": "running"
}
```

### Metrics

**URL**: `GET /metrics`

**Example**:

```bash
curl http://localhost:8080/metrics
```

**Response**:

```json
{
  "active_connections": 2,
  "service": "websocket-sse-server"
}
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Unit Tests

```bash
pytest tests/unit/
```

### Run Integration Tests

```bash
pytest tests/integration/
```

### Run with Coverage

```bash
pytest --cov=src/websocket_sse_server --cov-report=html
```

## Bidirectional Communication Example

### 1. Start the Server

```bash
uvicorn src.websocket_sse_server.main:app --reload
```

### Request-Response Flow (Direct Response Streaming)

#### 2. Send Request with Immediate Response Streaming

Send a request and immediately receive the WebSocket response:

```bash
# Terminal 1: Send request and stream response
curl -X POST http://localhost:8080/sse/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "data": {
      "message": "Please process this and send a response",
      "action": "request",
      "correlation_id": "req_456"
    }
  }'
```

#### 3. Connect WebSocket Client (in another terminal)

```bash
# Terminal 2: Connect WebSocket
wscat -c "ws://localhost:8080/ws?user_id=user123"
```

#### 4. WebSocket Client Responds

In the wscat terminal, send a response:

```json
{
  "type": "response",
  "data": {
    "reply": "Processed your request successfully!",
    "original_request_id": "req_456"
  },
  "correlation_id": "req_456"
}
```

#### 5. Verify Response Delivered

Check that the response appears immediately in the curl terminal (Terminal 1) as an SSE event. If the response includes `"is_final": true`, the stream will automatically terminate.

## Manual Testing (Traditional Flow)

### 1. Start the Server

```bash
uvicorn src.websocket_sse_server.main:app --reload
```

### 2. Connect WebSocket Client

```bash
# Terminal 1: Connect WebSocket
wscat -c "ws://localhost:8080/ws?user_id=user1"
```

### 3. Push SSE Message

```bash
# Terminal 2: Push message
curl -X POST http://localhost:8080/sse/push \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "data": {"text": "Hello!"}}'
```

### 4. Verify Message Received

Check that the message appears in the wscat terminal.

## Error Handling

- **Duplicate Connection**: If a user tries to connect twice, the second connection is rejected with code 1008
- **Invalid Message**: Messages with invalid format are rejected with 422 status code
- **User Not Connected**: Messages for disconnected users are dropped (optional: can be queued)
- **Connection Errors**: WebSocket errors are logged and connections are cleaned up

## Security

- CORS is configurable via `CORS_ORIGINS` environment variable
- User ID is extracted from URL query parameter
- No authentication is included (add as needed)

## Production Considerations

1. **Load Balancing**: Use multiple instances with Redis for connection state
2. **Monitoring**: Add metrics collection (Prometheus, Grafana)
3. **Logging**: Use structured logging (JSON format)
4. **SSL/TLS**: Use HTTPS/WSS in production
5. **Rate Limiting**: Add rate limiting for SSE endpoints
6. **Authentication**: Add JWT or OAuth2 authentication

## License

MIT
