# Architecture

The WebSocket SSE Server follows a modular architecture with clear separation of concerns.

## High-Level Architecture

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

## Component Architecture

### Main Application (`main.py`)
- Entry point for the FastAPI application
- Initializes global instances of ConnectionManager and SSEHandler
- Sets up routers and middleware
- Manages application lifecycle

### Configuration (`config.py`)
- Defines application settings using Pydantic Settings
- Handles environment variables
- Implements validation for configuration values
- Manages public account configurations

### Core Components

#### Connection Manager (`core/connection_manager.py`)
- Thread-safe WebSocket connection management
- Maintains user-to-websocket mappings
- Handles connection lifecycle (connect, disconnect)
- Provides methods for sending messages to specific users or broadcasting

#### SSE Handler (`core/sse_handler.py`)
- Processes incoming SSE messages
- Routes messages to appropriate WebSocket connections
- Manages request-response flows with correlation IDs
- Handles public account @mention routing

### API Endpoints

#### WebSocket Endpoints (`api/websocket_endpoints.py`)
- Handles WebSocket connections with user ID extraction
- Manages message reception and forwarding
- Integrates with SSE handler for response routing

#### SSE Endpoints (`api/sse_endpoints.py`)
- Receives SSE messages from upstream services
- Provides endpoints for both push and request-response flows
- Handles batch message processing

### Models (`models/message.py`)
- Pydantic models for message validation
- Ensures consistent message format

### Utilities
- Logger configuration with structured logging
- Custom exceptions for specific error conditions

## Data Flow

### From SSE to WebSocket
1. Upstream service sends SSE message to `/sse/push` or `/sse/send`
2. SSE endpoint validates message using Pydantic model
3. SSE handler processes message and checks for @mentions
4. Message is forwarded to appropriate WebSocket connection
5. (For request-response) SSE handler sets up response queue

### From WebSocket to SSE
1. WebSocket client sends message to server
2. Message is parsed and validated
3. If correlation ID exists, message is forwarded to SSE response queue
4. SSE client receives response via streaming

## Security Considerations

- CORS configuration limits allowed origins
- User ID extracted from query parameters (should be authenticated in production)
- Input validation through Pydantic models
- Rate limiting should be added in production environments