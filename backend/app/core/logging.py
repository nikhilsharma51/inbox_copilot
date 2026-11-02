

import json
import logging
import time
import uuid
from typing import Any, Callable

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


def scrub_sensitive_keys(logger: Any, method_name: str, event_dict: dict) -> dict:
    sensitive_keys = {
        "authorization",
        "token",
        "password",
        "cookie",
        "body",
        "credit_card",
        "ssn",
        "api_key",
        "secret",
        "refresh_token",
        "access_token",
        "id_token",
        "encrypted_refresh_token",
    }

    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "[REDACTED]"

    return event_dict


def configure_logging(log_level: str, log_format: str) -> None:
    
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Shared processors (order matters)
    shared_processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        scrub_sensitive_keys,  # Remove sensitive data
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # JSON output
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Human-readable text output
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Set root logger level
    logging.basicConfig(level=level)


def get_logger(name: str = __name__):
    return structlog.get_logger(name)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or extracts a request ID.

    Sets X-Request-ID header (generates one if not present) and stores in request scope.
    All logs include this ID for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process request and add request ID to scope and response."""
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in scope for access by handlers and logs
        request.scope["request_id"] = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs incoming requests and outgoing responses.

    Logs include method, path, status code, latency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Log request and response."""
        logger = get_logger("http")
        request_id = request.scope.get("request_id", "unknown")

        # Log incoming request
        logger.info(
            "request.start",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )

        # Process request and measure latency
        start_time = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start_time) * 1000

        # Log outgoing response
        logger.info(
            "request.complete",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
            request_id=request_id,
        )

        return response
