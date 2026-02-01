# Configuration

This document describes all configuration options available for the WebSocket SSE Server.

## Environment Variables

The server can be configured using environment variables. Create a `.env` file in the project root or set these variables in your deployment environment.

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server to |
| `PORT` | `8080` | Port number to run the server on |
| `DEBUG` | `false` | Enable debug mode for additional logging |

### WebSocket Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_PATH` | `/ws` | Path for WebSocket connections |
| `WS_PING_INTERVAL` | `30` | Interval (seconds) for WebSocket ping messages |
| `WS_PING_TIMEOUT` | `10` | Timeout (seconds) for WebSocket ping responses |

### SSE Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SSE_PATH` | `/sse/push` | Path for SSE push endpoint |
| `SSE_BATCH_PATH` | `/sse/push/batch` | Path for SSE batch push endpoint |

### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `{time:YYYY-MM-DD HH:mm:ss} \| {level} \| {message}` | Format for log messages |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost,http://127.0.0.1,https://localhost,https://127.0.0.1` | Comma-separated list of allowed origins for CORS |

### Public Accounts Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_ACCOUNTS` | (empty) | Comma-separated list of public accounts that can receive messages via @mentions |

## Configuration Validation

The server performs validation on configuration values:

- Host must be a valid hostname or IP address
- Port must be between 1 and 65535
- Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
- CORS origins must be valid URLs or "*" (wildcard)
- Public accounts must be valid identifiers

## Example Configuration

### Development `.env` file

```env
# Server
HOST=0.0.0.0
PORT=8080
DEBUG=true

# WebSocket
WS_PATH=/ws
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=10

# SSE
SSE_PATH=/sse/push
SSE_BATCH_PATH=/sse/push/batch

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT={time:YYYY-MM-DD HH:mm:ss} | {level} | {message}

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Public accounts
PUBLIC_ACCOUNTS=ci_bot,email_bot,notification_bot,system_bot
```

### Production `.env` file

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

# Security - restrict to your domains only
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Public accounts
PUBLIC_ACCOUNTS=ci_bot,email_bot,notification_bot
```

## Programmatic Configuration

Configuration is handled through the `Settings` class in `src/websocket_sse_server/config.py`. You can extend this class to add additional configuration options:

```python
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # Existing settings...
    
    # Add new settings as needed
    max_connections: int = 1000
    message_queue_size: int = 100
    
    @field_validator('max_connections')
    @classmethod
    def validate_max_connections(cls, v):
        if v <= 0:
            raise ValueError('Max connections must be positive')
        return v
```

## Configuration Loading Priority

Configuration values are loaded with the following priority (highest to lowest):

1. Environment variables
2. `.env` file in the project root
3. Default values in the Settings class

## Configuration Testing

To verify your configuration is loaded correctly, you can check the server logs at startup or create a simple test script:

```python
from src.websocket_sse_server.config import settings

print("Current configuration:")
print(f"Host: {settings.host}")
print(f"Port: {settings.port}")
print(f"CORS Origins: {settings.cors_origins}")
print(f"Debug Mode: {settings.debug}")
```

## Configuration Best Practices

1. **Security**: Never use wildcard CORS origins (`*`) in production
2. **Performance**: Adjust WebSocket ping intervals based on client requirements
3. **Logging**: Use appropriate log levels for different environments
4. **Validation**: Always validate configuration values before deployment
5. **Documentation**: Document custom configuration options in this file