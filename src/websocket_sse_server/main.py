"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api.websocket_endpoints import router as ws_router
from .api.sse_endpoints import router as sse_router
from .core.connection_manager import ConnectionManager
from .core.sse_handler import SSEHandler
from .config import settings
from .utils.logger import contextual_logger as logger

# Global instances
connection_manager = ConnectionManager()
sse_handler = SSEHandler(connection_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting WebSocket-SSE Server...", component="lifespan")

    yield

    logger.info("Shutting down WebSocket-SSE Server...", component="lifespan")
    # Cleanup resources
    await connection_manager.cleanup()


app = FastAPI(
    title="WebSocket SSE Server",
    description="WebSocket server with SSE endpoint support for upstream messages",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ws_router, prefix="")  # No prefix needed since ws_router already defines /ws
app.include_router(sse_router, prefix="")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    connections = connection_manager.get_connection_count()
    logger.info("Health check requested", endpoint="/health", connections=connections)
    return {
        "status": "healthy",
        "connections": connections,
        "uptime": "running"
    }


@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    connections = connection_manager.get_connection_count()
    logger.info("Metrics requested", endpoint="/metrics", connections=connections)
    return {
        "active_connections": connections,
        "service": "websocket-sse-server"
    }
