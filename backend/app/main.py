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
    status: str
    environment: str


class ReadyResponse(BaseModel):
    status: str
    database: str = "ok"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "app.startup",
        environment=settings.environment,
        debug=settings.environment == "dev",
    )

    yield

    logger.info("app.shutdown")



def create_app() -> FastAPI:

    configure_logging(settings.log_level, settings.log_format)

    app = FastAPI(
        title="Inbox Copilot API",
        description="AI-powered Gmail agent with human approval",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)

    app.add_middleware(RequestLoggingMiddleware)

    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    from fastapi.middleware.trustedhost import TrustedHostMiddleware

    trusted_hosts = [h.split(":")[0] for h in settings.cors_origins]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> HealthResponse:
        return HealthResponse(status="ok", environment=settings.environment)

    @app.get("/readyz", tags=["health"])
    async def readyz() -> ReadyResponse:
        return ReadyResponse(status="ok", database="ok")

    logger.info("app.created", environment=settings.environment)

    return app


app = create_app()
