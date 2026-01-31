# WebSocket SSE Server

A FastAPI-based WebSocket server with SSE (Server-Sent Events) endpoints for receiving upstream messages and forwarding them to connected WebSocket clients based on user ID.

## Overview

This server provides:
- **WebSocket connections** for real-time client communication
- **SSE endpoints** for receiving messages from upstream services
- **User-based routing** - messages are routed to WebSocket clients based on user ID
- **Connection management** - handles concurrent connections with thread safety
- **Batch message support** - process multiple messages in a single request

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   Upstream      │         │   WebSocket     │
│   Service       │         │   Clients       │
│                 │         │                 │
│  POST /sse/push │         │  WS /ws?user_id │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │  FastAPI Server │
            │                 │
            │  SSE Handler    │
            │  Connection Mgr │
            └─────────────────┘
```

## Project Structure

```
src/
├── websocket_sse_server/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   ├── models/                    # Pydantic models
│   │   ├── message.py            # Message models
│   │   └── sse_event.py          # SSE event models
│   ├── core/                      # Core business logic
│   │   ├── connection_manager.py # WebSocket connection manager
│   │   ├── sse_handler.py        # SSE message processor
│   │   └── message_router.py     # Message routing logic
│   ├── api/                       # API endpoints
│   │   ├── websocket_endpoints.py # WebSocket routes
│   │   └── sse_endpoints.py      # SSE routes
│   └── utils/                     # Utilities
│       ├── logger.py             # Logging configuration
│       └── exceptions.py         # Custom exceptions
├── tests/                         # Tests
│   ├── test_connection_manager.py
│   ├── test_sse_handler.py
│   ├── test_message_router.py
│   └── integration/
│       ├── test_websocket_flow.py
│       └── test_sse_flow.py
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example                  # Environment variables template
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose
└── README.md
```

## Installation

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t websocket-sse-server .
docker run -p 8080:8080 websocket-sse-server
```

## Configuration

Create a `.env` file in the project root:

```env
# Server
HOST=0.0.0.0
PORT=8080
DEBUG=false

# WebSocket
WS_PATH=/ws
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10

# SSE
SSE_PATH=/sse/push
SSE_BATCH_PATH=/sse/push/batch

# Logging
LOG_LEVEL=INFO
LOG_FORMAT={time:YYYY-MM-DD HH:mm:ss} | {level} | {message}

# Security
CORS_ORIGINS=*
```

## Usage

### 1. Start the Server

```bash
# Development mode with auto-reload
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080 --reload

# Production mode
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
```

### 2. Connect WebSocket Client

#### Using wscat

```bash
wscat -c "ws://localhost:8080/ws?user_id=test123"
```

#### Using JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8080/ws?user_id=test123');

ws.onopen = () => {
    console.log('Connected to server');
    ws.send('Hello server');
};

ws.onmessage = (event) => {
    console.log('Received:', event.data);
};

ws.onclose = () => {
    console.log('Disconnected');
};
```

#### Using Python

```python
import asyncio
import websockets

async def connect():
    async with websockets.connect("ws://localhost:8080/ws?user_id=test123") as ws:
        await ws.send("Hello server")
        response = await ws.recv()
        print(f"Received: {response}")

asyncio.run(connect())
```

### 3. Push Messages via SSE Endpoint

#### Single Message

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

#### Batch Messages

```bash
curl -X POST http://localhost:8080/sse/push/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"user_id": "test123", "data": {"msg": "msg1"}},
    {"user_id": "test456", "data": {"msg": "msg2"}}
  ]'
```

### 4. Health Check

```bash
curl http://localhost:8080/health
```

### 5. Metrics

```bash
curl http://localhost:8080/metrics
```

## API Endpoints

### WebSocket Endpoint

**`GET /ws?user_id=<user_id>`**

Connect to the WebSocket server with a user ID.

**Query Parameters:**
- `user_id` (required): Unique identifier for the user

**Example:**
```
ws://localhost:8080/ws?user_id=user123
```

### SSE Endpoints

**`POST /sse/push`**

Push a single SSE message to a user.

**Request Body:**
```json
{
  "user_id": "string",
  "data": {},
  "event_type": "string (optional)",
  "event_id": "string (optional)",
  "timestamp": "number (optional)"
}
```

**Response:**
```json
{
  "status": "success | partial",
  "message": "string"
}
```

**`POST /sse/push/batch`**

Push multiple SSE messages.

**Request Body:**
```json
[
  {
    "user_id": "string",
    "data": {},
    "event_type": "string (optional)",
    "event_id": "string (optional)",
    "timestamp": "number (optional)"
  }
]
```

**Response:**
```json
{
  "results": [
    {
      "user_id": "string",
      "success": boolean
    }
  ]
}
```

### Utility Endpoints

**`GET /health`**

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "connections": 0,
  "uptime": "running"
}
```

**`GET /metrics`**

Metrics endpoint.

**Response:**
```json
{
  "active_connections": 0,
  "service": "websocket-sse-server"
}
```

## Testing

### Run Unit Tests

```bash
cd src
pytest tests/ -v
```

### Run Integration Tests

```bash
cd src
pytest tests/integration/ -v
```

### Run All Tests with Coverage

```bash
cd src
pytest --cov=websocket_sse_server --cov-report=html
```

## Development

### Code Style

```bash
# Format code with black
black src/

# Lint with flake8
flake8 src/

# Type check with mypy
mypy src/
```

### Pre-commit Hooks (Optional)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: 1.7.1
    hooks:
      - id: mypy
```

## Production Deployment

### Environment Variables

Set production environment variables:

```bash
export HOST=0.0.0.0
export PORT=8080
export LOG_LEVEL=INFO
export CORS_ORIGINS=https://yourdomain.com
```

### Using Gunicorn (Recommended for Production)

```bash
pip install gunicorn uvicorn[standard]

gunicorn src.websocket_sse_server.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080 \
  --access-logfile - \
  --error-logfile -
```

### Docker Compose with Health Check

```yaml
version: '3.8'

services:
  websocket-sse-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - HOST=0.0.0.0
      - PORT=8080
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=https://yourdomain.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Troubleshooting

### Connection Issues

1. **Port already in use**: Change the port in `.env` or stop the conflicting service
2. **CORS errors**: Update `CORS_ORIGINS` in `.env` to include your client domain
3. **WebSocket connection rejected**: Check if user_id is already connected

### Message Delivery Issues

1. **User not connected**: Verify the user is connected via WebSocket before pushing messages
2. **Invalid message format**: Ensure the message follows the SSEMessage schema
3. **Connection dropped**: Check server logs for error details

### Performance Issues

1. **High memory usage**: Monitor connection count and consider connection limits
2. **Slow message delivery**: Check network latency and server resources

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
