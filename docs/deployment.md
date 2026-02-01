# Deployment Guide

This guide covers different deployment options for the WebSocket SSE Server.

## Prerequisites

- Python 3.10+
- pip or uv for package management
- Docker and Docker Compose (for containerized deployment)

## Local Deployment

### Using pip

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd websocket-sse-server
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

5. Run the server:
   ```bash
   uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
   ```

### Using pyproject.toml

1. Clone the repository and navigate to the project directory
2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the server:
   ```bash
   uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
   ```

## Containerized Deployment

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t websocket-sse-server .
   ```

2. Run the container:
   ```bash
   docker run -p 8080:8080 \
     -e HOST=0.0.0.0 \
     -e PORT=8080 \
     -e LOG_LEVEL=INFO \
     websocket-sse-server
   ```

### Using Docker Compose

1. Update `docker-compose.yml` with your environment variables if needed
2. Run the service:
   ```bash
   docker-compose up -d
   ```

## Production Deployment Considerations

### Process Management

For production deployments, use a process manager like systemd, supervisor, or pm2-equivalent for Python.

Example systemd service file (`/etc/systemd/system/websocket-sse-server.service`):
```ini
[Unit]
Description=WebSocket SSE Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/websocket-sse-server
ExecStart=/path/to/venv/bin/uvicorn src.websocket_sse_server.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable websocket-sse-server
sudo systemctl start websocket-sse-server
```

### Reverse Proxy Setup

Use nginx or Apache as a reverse proxy for production deployments:

Nginx configuration example:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS

For production, always use HTTPS. You can:
- Configure SSL in your reverse proxy (recommended)
- Use a service like Let's Encrypt for free certificates

### Scaling Considerations

For high-availability and scaling:

1. **Load Balancer**: Use a load balancer to distribute connections
2. **Shared State**: For multiple instances, implement shared connection state using Redis
3. **Message Queue**: Implement a message queue system for reliable message delivery between instances

Example with Redis for shared state (requires code modification):

```python
# In config.py, add Redis settings
redis_host: str = "localhost"
redis_port: int = 6379
```

## Environment Variables

Configure the server using environment variables in a `.env` file:

```bash
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
CORS_ORIGINS=http://localhost,http://127.0.0.1,https://localhost,https://127.0.0.1

# Public accounts configuration
PUBLIC_ACCOUNTS=ci_bot,email_bot,notification_bot
```

## Monitoring and Logging

### Logging

The server uses structured logging with loguru. Logs are output to stdout and optionally to a file when DEBUG=true.

### Health Checks

Monitor the `/health` endpoint to check server status:
```bash
curl http://your-server/health
```

Expected response:
```json
{
  "status": "healthy",
  "connections": 5,
  "uptime": "running"
}
```

### Metrics

Use the `/metrics` endpoint for monitoring:
```bash
curl http://your-server/metrics
```

Expected response:
```json
{
  "active_connections": 5,
  "service": "websocket-sse-server"
}
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**:
   - Check CORS settings
   - Verify proxy configuration supports WebSocket upgrades
   - Ensure firewall allows WebSocket connections

2. **High Memory Usage**:
   - Monitor connection count via metrics endpoint
   - Implement connection timeouts
   - Check for connection leaks

3. **Message Delivery Failures**:
   - Verify target user is connected
   - Check logs for error messages
   - Validate message format

### Debugging

Enable debug mode by setting `DEBUG=true` in your environment to get more detailed logs.

### Performance Tuning

- Adjust `WS_PING_INTERVAL` and `WS_PING_TIMEOUT` based on your needs
- Monitor resource usage under load
- Consider connection pooling for database integrations (if added)