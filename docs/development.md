# Development Guide

This guide provides information for developers contributing to the WebSocket SSE Server.

## Setting Up Development Environment

### Prerequisites

- Python 3.10+
- pip or uv package manager
- Git

### Initial Setup

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
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
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
├── docs/                           # Documentation
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Code Standards

### Python Standards

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public classes and functions
- Keep functions focused and small (< 50 lines when possible)

### Naming Conventions

- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Import Organization

Follow the standard import grouping:
1. Standard library imports
2. Third-party imports
3. First-party imports (local project)
4. Local application imports

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/websocket_sse_server --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_connection_manager.py
```

Run specific test:
```bash
pytest tests/unit/test_connection_manager.py::TestConnectionManager::test_connect_new_user
```

### Test Structure

- Unit tests in `tests/unit/` - test individual components in isolation
- Integration tests in `tests/integration/` - test component interactions
- End-to-end tests in `tests/e2e/` - test complete workflows

### Writing Tests

All new features should include appropriate tests:

```python
import pytest
from unittest.mock import AsyncMock
from websocket_sse_server.core.connection_manager import ConnectionManager

@pytest.mark.asyncio
async def test_send_to_user_success():
    """Test sending message to connected user."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()
    
    await manager.connect("user1", mock_websocket)
    
    message = {"text": "Hello"}
    result = await manager.send_to_user("user1", message)
    
    assert result is True
    mock_websocket.send_json.assert_called_once_with(message)
```

## Adding New Features

### Adding a New API Endpoint

1. Create the endpoint function in the appropriate module in `src/websocket_sse_server/api/`
2. Add the route to the router
3. Create corresponding tests in the `tests/` directory
4. Update documentation in the `docs/` directory

### Adding a New Configuration Option

1. Add the option to the `Settings` class in `src/websocket_sse_server/config.py`
2. Add validation if needed using Pydantic validators
3. Update `.env.example` with the new option
4. Update documentation

### Adding New Model Validation

1. Define the model in `src/websocket_sse_server/models/`
2. Add validation rules using Pydantic
3. Create tests for the validation

## Running the Development Server

```bash
uvicorn src.websocket_sse_server.main:app --reload --host 0.0.0.0 --port 8080
```

The `--reload` flag enables auto-reload on code changes.

## Code Quality Tools

### Formatting

Format code with Black:
```bash
black src/ tests/
```

### Linting

Lint code with Flake8:
```bash
flake8 src/ tests/
```

### Type Checking

Check types with MyPy:
```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run all tests to ensure nothing is broken
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Common Development Tasks

### Adding Dependencies

Add runtime dependencies to `pyproject.toml` and `requirements.txt`:
```toml
dependencies = [
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    # Add new dependency here
]
```

Add development dependencies to `pyproject.toml` and `requirements-dev.txt`:
```toml
dev = [
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1",
    # Add new dev dependency here
]
```

### Updating Documentation

Update documentation in the `docs/` directory when:
- Adding new features
- Changing API endpoints
- Modifying configuration options
- Updating architecture

### Debugging Tips

1. Enable debug logging by setting `DEBUG=true` in your environment
2. Use the `/health` and `/metrics` endpoints to monitor server status
3. Check structured logs for detailed information about requests and errors
4. Use the example bidirectional demo to test functionality: `python example_bidirectional_demo.py`

## Performance Considerations

When developing new features, consider:

- Minimize lock contention in concurrent code
- Use async/await appropriately
- Validate inputs early to prevent processing invalid data
- Implement proper error handling and recovery
- Monitor memory usage with many concurrent connections