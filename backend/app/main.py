"""
FastAPI application factory.

This module creates the main FastAPI app with:
- Lifespan hooks for startup/shutdown
- Middleware stack (request ID, logging, error handling, CORS)
- Health check endpoints
- Exception handlers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.core.errors import AppError, app_error_handler, general_exception_handler
from app.core.logging import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    configure_logging,
    get_logger,
)

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str
    database: str = "ok"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown logic.
    """
    # Startup
    logger.info(
        "app.startup",
        environment=settings.environment,
        debug=settings.environment == "dev",
    )

    # TODO: In Step 5, initialize database engine here
    # from app.db.session import init_db
    # await init_db()

    yield

    # Shutdown
    logger.info("app.shutdown")

    # TODO: In Step 5, close database here
    # from app.db.session import close_db
    # await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure logging early
    configure_logging(settings.log_level, settings.log_format)

    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Inbox Copilot API",
        description="AI-powered Gmail agent with human approval",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware stack (order matters)
    # 1. Request ID middleware (must be first to add ID to scope)
    app.add_middleware(RequestIDMiddleware)

    # 2. Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # 3. CORS middleware (from FastAPI, must be after other middleware)
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # 4. Security headers middleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware

    trusted_hosts = [h.split(":")[0] for h in settings.cors_origins]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Exception handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Health check endpoints
    @app.get("/healthz", tags=["health"])
    async def healthz() -> HealthResponse:
        """
        Health check endpoint.

        Returns 200 OK if the process is up.
        """
        return HealthResponse(status="ok", environment=settings.environment)

    @app.get("/readyz", tags=["health"])
    async def readyz() -> ReadyResponse:
        """
        Readiness check endpoint.

        Returns 200 OK if the app is ready to handle requests (DB is reachable).
        """
        return ReadyResponse(status="ok", database="ok")

    logger.info("app.created", environment=settings.environment)

    return app


# Create the app instance
app = create_app()
