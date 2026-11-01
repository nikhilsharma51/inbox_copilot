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

    # Relationships
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")
    mailboxes: Mapped[list["Mailbox"]] = relationship("Mailbox", back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Session(Base):
    """Server-side session for authenticated users."""

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
    """Gmail mailbox connection per user."""

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
    """Email category for filtering/classification."""

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
    """Background job for async work (sync, classify, draft, etc.)."""

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
    """Immutable append-only audit log (cannot be updated or deleted)."""

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
