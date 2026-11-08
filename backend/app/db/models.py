"""
SQLAlchemy 2.0 async ORM models for the application.

Phase 0 models:
- users, sessions, mailboxes, categories, jobs, job_events, audit_log, system_flags

All timestamps are timestamptz (timezone-aware).
Primary keys are UUIDs unless noted.
User-owned tables carry user_id and query results are scoped by it.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class User(Base):
    """User account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    style_preset: Mapped[str] = mapped_column(
        Enum("formal", "friendly", "brief", name="style_preset"), default="formal"
    )
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    label_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")
    mailboxes: Mapped[list["Mailbox"]] = relationship("Mailbox", back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(256), primary_key=True)  # Hashed session ID
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Hashed IP
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id[:8]}..., user_id={self.user_id})>"


class Mailbox(Base):

    __tablename__ = "mailboxes"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(
        Enum("gmail", "demo", "outlook", name="provider"), default="gmail"
    )
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_refresh_token: Mapped[bytes | None] = mapped_column(nullable=True)  # nonce + ciphertext
    key_version: Mapped[int | None] = mapped_column(nullable=True)  # For key rotation
    scopes: Mapped[list[str]] = mapped_column(JSON, default=[])  # Granted OAuth scopes
    history_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Gmail sync cursor
    status: Mapped[str] = mapped_column(
        Enum(
            "connected", "needs_reconnect", "revoked", "disconnected",
            name="mailbox_status"
        ),
        default="connected",
    )
    sync_status: Mapped[str] = mapped_column(
        Enum("idle", "backfilling", "syncing", "error", name="sync_status"),
        default="idle",
    )
    backfill_days: Mapped[int] = mapped_column(default=30)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mailboxes")

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_mailbox_user_provider"),)

    def __repr__(self) -> str:
        return f"<Mailbox(id={self.id}, email={self.email_address}, status={self.status})>"


class Category(Base):

    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Up to 3 examples
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color
    sort_order: Mapped[int] = mapped_column(default=0)
    gmail_label_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_category_user_slug"),)

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, user_id={self.user_id}, slug={self.slug})>"


class Job(Base):

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default={})
    status: Mapped[str] = mapped_column(
        Enum("queued", "running", "succeeded", "failed", "cancelled", "dead", name="job_status"),
        default="queued",
        index=True,
    )
    priority: Mapped[int] = mapped_column(default=0)
    attempts: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)
    run_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(
        String(256), nullable=True, unique=True, index=True
    )  # For deduplication
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    mailbox_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("mailboxes.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.type}, status={self.status})>"


class JobEvent(Base):
    """Event stream for a job (for SSE streaming to frontend)."""

    __tablename__ = "job_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # progress, error, completed
    data: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<JobEvent(id={self.id}, job_id={self.job_id}, type={self.type})>"


class AuditLog(Base):

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default={})  # No full bodies
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA256 of previous row
    row_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA256 of this row
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, event={self.event_type})>"


class SystemFlag(Base):
    """System-wide configuration flags (kill switch, budgets, etc.)."""

    __tablename__ = "system_flags"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default={})
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<SystemFlag(key={self.key})>"

class Thread(Base):
    """Email thread with classification status."""

    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    mailbox_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    gmail_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)

    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snippet: Mapped[str | None] = mapped_column(String(500), nullable=True)
    participants: Mapped[list[dict]] = mapped_column(JSON, default=list)

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    message_count: Mapped[int] = mapped_column(default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    classified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    class_status: Mapped[str] = mapped_column(
        String(50),
        default="unreviewed",
        index=True
    )
    category_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )

    priority: Mapped[int | None] = mapped_column(default=None)  # Range: 1-4
    confidence: Mapped[float | None] = mapped_column(default=None)  # Range: 0.0-1.0
    summary: Mapped[str | None] = mapped_column(String(160), nullable=True)
    needs_reply: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "mailbox_id",
            "gmail_thread_id",
            name="uq_thread_mailbox_gmail_id"
        ),
        Index("idx_threads_mailbox_classified", "mailbox_id", "classified_at"),
        Index("idx_threads_mailbox_class_status", "mailbox_id", "class_status"),
        Index("idx_threads_mailbox_category", "mailbox_id", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<Thread(id={self.id}, subject={self.subject})>"


class AgentRun(Base):
    """Record of LLM executions for auditing and usage tracking."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    mailbox_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    thread_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="SET NULL"),
        nullable=True
    )

    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)

    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    latency_ms: Mapped[int] = mapped_column(default=0)

    redacted_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("idx_agent_runs_user_mailbox", "user_id", "mailbox_id"),
        Index("idx_agent_runs_kind", "kind"),
    )

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, kind={self.kind}, model={self.model})>"


class UsageDaily(Base):
    """Track daily token usage and email activity per user."""

    __tablename__ = "usage_daily"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    tokens_in: Mapped[int] = mapped_column(default=0)
    tokens_out: Mapped[int] = mapped_column(default=0)
    sends_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_usage_user_date"),
        Index("idx_usage_user_date", "user_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<UsageDaily(user_id={self.user_id}, date={self.date})>"


class Correction(Base):
    """Store user corrections to improve email classification."""

    __tablename__ = "corrections"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    thread_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False
    )

    predicted_category_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    corrected_category_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("idx_corrections_user_thread", "user_id", "thread_id"),
    )

    def __repr__(self) -> str:
        return f"<Correction(id={self.id}, user_id={self.user_id})>"