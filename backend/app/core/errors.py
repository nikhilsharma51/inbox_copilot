"""
Error handling and exception hierarchy.

All exceptions are mapped to HTTP status codes and JSON responses.
Sensitive data (stack traces) is never leaked to clients.
"""

from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    details: str | None = None
    request_id: str | None = None


class AppError(Exception):
    """Base application error."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize error."""
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(AppError):
    """Request validation failed."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    """Authentication failed (missing or invalid credentials)."""

    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    """User lacks permission for this resource."""

    status_code = HTTPStatus.FORBIDDEN
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(AppError):
    """Resource not found."""

    status_code = HTTPStatus.NOT_FOUND
    error_code = "NOT_FOUND"


class ConflictError(AppError):
    """Resource already exists or operation conflicts."""

    status_code = HTTPStatus.CONFLICT
    error_code = "CONFLICT"


class RateLimitError(AppError):
    """Rate limit exceeded."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"


class InternalServerError(AppError):
    """Internal server error."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code = "INTERNAL_SERVER_ERROR"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions and return JSON response."""
    request_id = request.scope.get("request_id")

    response = ErrorResponse(
        error=exc.error_code,
        details=exc.details or exc.message,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True),
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions (catch-all)."""
    request_id = request.scope.get("request_id")

    response = ErrorResponse(
        error="INTERNAL_SERVER_ERROR",
        details="An unexpected error occurred. Please try again later.",
        request_id=request_id,
    )

    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True),
    )
