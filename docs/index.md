# WebSocket SSE Server Documentation

Welcome to the WebSocket SSE Server documentation. This project provides bidirectional communication between Server-Sent Events (SSE) and WebSocket connections.

## Table of Contents

- [Overview](overview.md)
- [Architecture](architecture.md)
- [API Reference](api.md)
- [Configuration](configuration.md)
- [Deployment](deployment.md)
- [Development](development.md)
- [Troubleshooting](troubleshooting.md)

## Quick Start

For a quick start with the project, see our [Overview](overview.md) section.

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
- **Public Account Mentions**: Support for @mentions of public accounts