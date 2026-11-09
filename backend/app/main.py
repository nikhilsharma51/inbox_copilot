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
from ai_pipeline.sync import sync_mailbox
from ai_pipeline.classify import classify_batch
from app.services.categories import create_category, list_categories, archive_category
from app.services.corrections import record_correction

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
    
    
@app.post("/api/mailboxes/{mailbox_id}/sync")
async def trigger_sync(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    mailbox = await session.get(Mailbox, mailbox_id)

    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(404, "Mailbox not found")

    background_tasks.add_task(sync_mailbox, mailbox_id, session)

    return {"status": "syncing"}


@app.get("/api/mailboxes/{mailbox_id}/status")
async def get_sync_status(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    mailbox = await session.get(Mailbox, mailbox_id)

    if not mailbox or mailbox.user_id != current_user.id:
        raise HTTPException(404, "Mailbox not found")

    total = await session.execute(
        select(func.count(Thread.id)).where(
            Thread.mailbox_id == mailbox_id
        )
    )
    total_count = total.scalar() or 0

    classified = await session.execute(
        select(func.count(Thread.id)).where(
            and_(
                Thread.mailbox_id == mailbox_id,
                Thread.classified_at.isnot(None)
            )
        )
    )
    classified_count = classified.scalar() or 0

    return {
        "sync_status": mailbox.sync_status,
        "last_sync_at": mailbox.last_sync_at,
        "classified": classified_count,
        "total": total_count
    }


@app.post("/api/categories")
async def create_new_category(
    req: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    from app.services.categories import create_category

    try:
        cat = await create_category(
            current_user.id,
            req["name"],
            req["slug"],
            req["description"],
            req.get("color"),
            session
        )
        return cat

    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/categories")
async def list_user_categories(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    from app.services.categories import list_categories

    cats = await list_categories(current_user.id, session)

    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description
        }
        for c in cats
    ]


@app.get("/api/threads")
async def list_threads(
    mailbox_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    class_status: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Thread).join(Mailbox)

    if mailbox_id:
        query = query.where(Thread.mailbox_id == mailbox_id)

    if category_id:
        query = query.where(Thread.category_id == category_id)

    if class_status:
        query = query.where(Thread.class_status == class_status)

    query = query.where(Mailbox.user_id == current_user.id)

    query = query.order_by(
        Thread.last_message_at.desc(),
        Thread.id.desc()
    )
    query = query.limit(limit + 1)

    result = await session.execute(query)
    threads = result.scalars().all()

    has_next = len(threads) > limit
    threads = threads[:limit]

    return {
        "threads": [
            {
                "id": t.id,
                "subject": t.subject,
                "snippet": t.snippet,
                "category_id": t.category_id,
                "priority": t.priority,
                "confidence": t.confidence,
                "class_status": t.class_status,
                "summary": t.summary,
                "needs_reply": t.needs_reply,
                "last_message_at": t.last_message_at
            }
            for t in threads
        ],
        "has_next": has_next
    }


@app.get("/api/threads/{thread_id}")
async def get_thread_detail(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    thread = await session.execute(
        select(Thread).join(Mailbox).where(
            and_(
                Thread.id == thread_id,
                Mailbox.user_id == current_user.id
            )
        )
    )

    thread = thread.scalars().first()

    if not thread:
        raise HTTPException(404, "Thread not found")

    return {
        "id": thread.id,
        "subject": thread.subject,
        "snippet": thread.snippet,
        "participants": thread.participants,
        "category_id": thread.category_id,
        "priority": thread.priority,
        "confidence": thread.confidence,
        "class_status": thread.class_status,
        "summary": thread.summary,
        "needs_reply": thread.needs_reply,
        "last_message_at": thread.last_message_at
    }


@app.patch("/api/threads/{thread_id}/category")
async def update_thread_category(
    thread_id: UUID,
    req: dict,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    from app.services.corrections import record_correction

    try:
        correction = await record_correction(
            current_user.id,
            thread_id,
            UUID(req["category_id"]),
            req.get("reason"),
            session
        )

        thread = await session.get(Thread, thread_id)

        return {
            "id": thread.id,
            "category_id": thread.category_id,
            "class_status": thread.class_status
        }

    except ValueError as e:
        raise HTTPException(404, str(e))


    logger.info("app.created", environment=settings.environment)

    return app


app = create_app()
