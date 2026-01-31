# WebSocket SSE Server

A FastAPI-based WebSocket server with SSE endpoint support for receiving upstream messages.

## Features

- **WebSocket Server**: Handle WebSocket connections with user ID extraction
- **SSE Endpoint**: HTTP endpoint for receiving upstream SSE messages
- **Message Routing**: Route messages to appropriate WebSocket connections based on user ID
- **Connection Management**: Thread-safe connection management with proper cleanup
- **Batch Support**: Support for batch message processing
- **Health Checks**: Health and metrics endpoints

## Architecture

```
┌─────────────────┐
│  Upstream       │
│  (SSE Producer) │
└────────┬────────┘
         │
         │ HTTP POST
         ▼
┌─────────────────┐
│  SSE Endpoint   │
│  (/sse/push)    │
└────────┬────────┘
         │
         │ Message Router
         ▼
┌─────────────────┐
│  Connection     │
│  Manager        │
└────────┬────────┘
         │
         │ WebSocket
         ▼
┌─────────────────┐
│  Client         │
│  (WebSocket)    │
└─────────────────┘
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
LOG_LEVEL=INFO
CORS_ORIGINS=*
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

### SSE Push Endpoint

**URL**: `POST /sse/push`

**Request Body**:

```json
{
  "user_id": "test123",
  "data": {"message": "Hello from upstream!", "type": "notification"},
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
    "data": {"message": "Hello from upstream!", "type": "notification"},
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

## Manual Testing

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
