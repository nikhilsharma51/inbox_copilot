from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.db import engine, Base
from app.routes.auth import router as auth_router
from app.routes.sync import router as sync_router
from app.routes.classify import router as classify_router
from app.routes.drafts import router as drafts_router
from app.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Inbox Copilot API",
        description="AI-powered Gmail agent with human approval",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(auth_router)
    app.include_router(sync_router)
    app.include_router(classify_router)
    app.include_router(drafts_router)
    app.include_router(chat_router)

    @app.get("/healthz", response_class=PlainTextResponse)
    async def healthz():
        return "ok"

    return app


app = create_app()
