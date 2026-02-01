# Troubleshooting

This guide helps troubleshoot common issues with the WebSocket SSE Server.

## Common Issues

### WebSocket Connection Failures

**Symptoms:**
- Clients cannot establish WebSocket connections
- Connection errors with codes like 1006
- Intermittent connection drops

**Solutions:**
1. Check CORS configuration in your environment variables:
   ```
   CORS_ORIGINS=http://yourdomain.com,https://yourdomain.com
   ```
   
2. Verify your reverse proxy (if using) supports WebSocket upgrades:
   - Nginx: Ensure `proxy_set_header Upgrade $http_upgrade` and `proxy_set_header Connection "upgrade"` are set
   - Apache: Enable mod_proxy_wstunnel

3. Check firewall settings allow WebSocket connections (typically same port as HTTP)

4. Verify the user_id parameter is properly included in the WebSocket URL:
   ```
   ws://yourserver/ws?user_id=unique_user_id
   ```

### Message Delivery Problems

**Symptoms:**
- Messages sent via SSE are not reaching WebSocket clients
- Responses from WebSocket clients are not returned via SSE

**Solutions:**
1. Verify the target user is connected to a WebSocket:
   - Check `/metrics` endpoint for active connection count
   - Ensure user connected with the same user_id used in the SSE message

2. Check server logs for error messages:
   ```bash
   # Look for messages about failed deliveries
   ```

3. Validate message format matches the expected schema:
   ```json
   {
     "user_id": "target_user",
     "data": {"message": "Hello"},
     "event_type": "message"
   }
   ```

### Server Performance Issues

**Symptoms:**
- High CPU or memory usage
- Slow response times
- Connection timeouts

**Solutions:**
1. Monitor active connections:
   ```bash
   curl http://yourserver/metrics
   ```

2. Adjust WebSocket ping settings:
   ```env
   WS_PING_INTERVAL=60  # Increase interval to reduce overhead
   WS_PING_TIMEOUT=15   # Adjust timeout as needed
   ```

3. Check system resources and scale if necessary

4. Review logs for repeated error messages that might indicate issues

### Duplicate Connection Errors

**Symptoms:**
- Error message "User already connected"
- Code 1008 on WebSocket connection attempts

**Solutions:**
1. Ensure proper connection cleanup in client applications
2. Implement client-side logic to handle connection state properly
3. Check that user_id values are unique and consistent across reconnects

## Debugging Steps

### Enable Debug Logging

Set `DEBUG=true` in your environment to get more detailed logs:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Check Server Status

1. Health check:
   ```bash
   curl http://yourserver/health
   ```

2. Metrics:
   ```bash
   curl http://yourserver/metrics
   ```

### Verify Configuration

Check that your environment variables are correctly set:
```bash
# Example check
echo $HOST
echo $PORT
echo $CORS_ORIGINS
```

### Test Individual Components

1. Test WebSocket connection separately:
   ```bash
   # Using wscat or similar tool
   wscat -c "ws://yourserver/ws?user_id=test123"
   ```

2. Test SSE endpoint separately:
   ```bash
   curl -X POST http://yourserver/sse/push \
     -H "Content-Type: application/json" \
     -d '{"user_id": "test123", "data": {"message": "test"}}'
   ```

## Log Analysis

### Common Log Messages

- `"User connected"` - Successful WebSocket connection
- `"User disconnected"` - WebSocket connection closed
- `"Message sent to user"` - Successful message delivery
- `"Attempt to send message to disconnected user"` - Target user not connected
- `"Error sending to user"` - Failed to send message due to connection issue
- `"Processing SSE message"` - SSE message received and processed
- `"Detected @mention of public account"` - Public account @mention detected

### Error Patterns

Look for these patterns in logs:
- Repeated connection/disconnection cycles
- Multiple "User already connected" errors
- "Error sending to user" followed by connection cleanup
- Validation errors for message format

## Configuration Issues

### Invalid CORS Origins

**Problem:** Error during startup about invalid CORS origin format

**Solution:** Ensure CORS_ORIGINS contains valid URLs:
```env
# Correct
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Incorrect (will cause validation error)
CORS_ORIGINS=localhost,invalid-url
```

### Port Conflicts

**Problem:** Server fails to start with "Address already in use" error

**Solution:**
1. Check if another instance is running:
   ```bash
   lsof -i :8080  # Replace 8080 with your port
   ```
2. Kill conflicting process or use a different port:
   ```env
   PORT=8081
   ```

## Network Issues

### Firewall Blocking

Ensure your firewall allows:
- The configured server port (default 8080)
- WebSocket upgrade requests (same port as HTTP)

### Proxy Configuration

If using a reverse proxy, ensure:
- WebSocket upgrade headers are properly configured
- Timeout settings accommodate long-lived connections
- Buffering is disabled for SSE endpoints

## Resource Issues

### Memory Leaks

Monitor memory usage and check for:
- Growing connection counts without corresponding disconnections
- Accumulation of message queues
- Retained references to disconnected clients

### Connection Limits

If experiencing connection limits:
- Check system file descriptor limits
- Monitor active connection count via `/metrics` endpoint
- Consider connection timeout mechanisms

## Testing Strategies

### Isolated Testing

1. Test WebSocket connections independently
2. Test SSE endpoints independently  
3. Test request-response flows
4. Test batch operations

### Load Testing

Use tools like `wrk` or `ab` to simulate multiple connections:
```bash
# Test HTTP endpoints
ab -n 1000 -c 10 http://yourserver/health

# For WebSocket load testing, consider tools like Artillery with WebSocket plugin
```

## Getting Help

When requesting help:

1. Include your configuration (with sensitive data redacted)
2. Provide relevant log snippets
3. Describe the expected vs. actual behavior
4. Mention your deployment environment (local, Docker, cloud)
5. Include the server version and Python version