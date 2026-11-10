import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://")

connect_args = {}
if "-pooler" in database_url:
    connect_args["prepare_threshold"] = None

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_sub = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    refresh_token_enc = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_category_user_name"),
    )


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    gmail_thread_id = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    needs_reply = Column(String, default="unknown")
    priority = Column(String, default="normal")
    confidence = Column(String, default="0.0")
    status = Column(String, default="unread")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_thread_id", name="uq_thread_user_gmail_id"),
    )


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    thread_id = Column(String, ForeignKey("threads.id"), nullable=False)
    to_addr = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
