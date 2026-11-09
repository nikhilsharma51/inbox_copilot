from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Inbox Copilot API",
        description="AI-powered Gmail agent with human approval",
        version="0.1.0",
    )

    @app.get("/healthz", response_class=PlainTextResponse)
    async def healthz():
        return "ok"

    return app


app = create_app()
