# WebSocket SSE Server - Project Context

## Project Overview

The WebSocket SSE Server is a Python-based FastAPI application that provides bidirectional communication between Server-Sent Events (SSE) and WebSocket connections. This enables real-time, bidirectional messaging between clients and services, bridging the gap between traditional WebSocket connections and Server-Sent Events for flexible communication patterns.

### Key Features
- WebSocket server with user ID extraction
- SSE endpoints for receiving upstream messages
- Bidirectional communication between SSE and WebSocket
- Message correlation using correlation IDs
- Message routing based on user ID
- Thread-safe connection management
- Batch message processing support
- Health checks and metrics endpoints
- Public account @mention functionality

### Architecture
The system consists of several core components:
- **Main Application**: FastAPI application entry point
- **Connection Manager**: Thread-safe WebSocket connection management
- **SSE Handler**: Processes incoming SSE messages and routes them to WebSocket connections
- **Configuration System**: Pydantic-based settings with validation
- **API Endpoints**: Separate modules for WebSocket and SSE endpoints
- **Models**: Pydantic models for message validation
- **Utilities**: Logging configuration and custom exceptions

## Building and Running

### Prerequisites
- Python 3.10+
- pip or uv package manager

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

Or using pyproject.toml:
```bash
pip install -e ".[dev]"
```

### Running the Server
Development mode:
```bash
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080 --reload
```

Production mode:
```bash
uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
```

### Docker Deployment
Build and run with Docker:
```bash
docker build -t websocket-sse-server .
docker run -p 8080:8080 websocket-sse-server
```

Or with docker-compose:
```bash
docker-compose up
```

## Configuration

The server is configured using environment variables defined in a `.env` file. Key configuration options include:

- `HOST` and `PORT`: Server binding
- `DEBUG`: Enable debug mode
- WebSocket settings: `WS_PATH`, `WS_PING_INTERVAL`, `WS_PING_TIMEOUT`
- SSE settings: `SSE_PATH`, `SSE_BATCH_PATH`
- Logging: `LOG_LEVEL`, `LOG_FORMAT`
- Security: `CORS_ORIGINS`
- Public accounts: `PUBLIC_ACCOUNTS`

Copy `.env.example` to `.env` to get started with default values.

## API Endpoints

### WebSocket
- `ws://<host>:<port>/ws?user_id=<user_id>` - WebSocket connection with user ID

### SSE Endpoints
- `POST /sse/send` - Send message with request-response flow
- `POST /sse/push` - Push one-way notification
- `POST /sse/push/batch` - Push multiple messages in batch

### Utility Endpoints
- `GET /health` - Health check
- `GET /metrics` - Server metrics

## Development Conventions

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public classes and functions
- Keep functions focused and small (< 50 lines when possible)

### Testing
Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/websocket_sse_server --cov-report=html
```

### Dependencies
Managed through `pyproject.toml` and synchronized with `requirements.txt`:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- Loguru: Structured logging
- Pytest: Testing framework

## Documentation

Comprehensive documentation is available in the `docs/` directory:
- [Overview](docs/overview.md) - Introduction to the project
- [Architecture](docs/architecture.md) - System architecture and components
- [API Reference](docs/api.md) - Detailed API documentation
- [Configuration](docs/configuration.md) - Configuration options and settings
- [Deployment](docs/deployment.md) - Deployment guides and best practices
- [Development](docs/development.md) - Development setup and contribution guidelines
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Testing

The project includes both unit and integration tests organized in the `tests/` directory:
- Unit tests in `tests/unit/` - Test individual components in isolation
- Integration tests in `tests/integration/` - Test component interactions
- Additional tests in `tests/` root - End-to-end and special case tests

Run tests with pytest:
```bash
pytest  # All tests
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only
```

## Special Features

### Public Account @Mentions
The system supports @mention functionality for public accounts (bots), allowing messages to be routed to designated accounts instead of the original recipient. This is configured via the `PUBLIC_ACCOUNTS` environment variable.

### Request-Response Flow
The `/sse/send` endpoint enables request-response patterns where an SSE message is sent to a WebSocket client and the response is streamed back via SSE.

### Connection Management
The ConnectionManager implements thread-safe operations for managing WebSocket connections, including proper cleanup and handling of duplicate connections.