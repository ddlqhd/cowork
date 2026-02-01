# Overview

The WebSocket SSE Server is a FastAPI-based server that provides bidirectional communication between Server-Sent Events (SSE) and WebSocket connections. This enables real-time, bidirectional messaging between clients and services.

## Purpose

This server bridges the gap between traditional WebSocket connections and Server-Sent Events, allowing for flexible communication patterns:

- Services can push messages to connected WebSocket clients via SSE endpoints
- WebSocket clients can send responses back that are streamed via SSE
- Supports both fire-and-forget messaging and request-response patterns

## Key Components

### Connection Manager
Manages WebSocket connections indexed by user ID, providing thread-safe operations for connecting, disconnecting, and sending messages to specific users.

### SSE Handler
Processes incoming SSE messages and routes them to appropriate WebSocket connections. Also handles the reverse flow from WebSocket responses back to SSE clients.

### Public Account System
Supports @mention functionality for public accounts (bots), allowing messages to be routed to designated accounts instead of the original recipient.

## Use Cases

- Real-time notifications and alerts
- Chat applications with bot integrations
- IoT device communication
- Live dashboard updates
- Collaborative applications