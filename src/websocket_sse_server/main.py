"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .api.websocket_endpoints import router as ws_router
from .api.sse_endpoints import router as sse_router
from .core.connection_manager import ConnectionManager
from .core.sse_handler import SSEHandler
from .config import settings
from .utils.logger import logger

# Global instances
connection_manager = ConnectionManager()
sse_handler = SSEHandler(connection_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting WebSocket-SSE Server...")

    yield

    logger.info("Shutting down WebSocket-SSE Server...")
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
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ws_router, prefix=settings.ws_path)
app.include_router(sse_router, prefix="")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "connections": connection_manager.get_connection_count(),
        "uptime": "running"
    }


@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return {
        "active_connections": connection_manager.get_connection_count(),
        "service": "websocket-sse-server"
    }
