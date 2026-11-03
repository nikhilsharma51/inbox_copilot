"""Mail backend implementations (Fake and Gmail)."""

from .base import (
    AuthExpired,
    BackendError,
    Draft,
    DraftIn,
    MailBackend,
    Message,
    NotFound,
    RateLimited,
    Thread,
    ThreadSummary,
)
from .fake import FakeBackend

__all__ = [
    "MailBackend",
    "FakeBackend",
    "Message",
    "ThreadSummary",
    "Thread",
    "Draft",
    "DraftIn",
    "BackendError",
    "NotFound",
    "AuthExpired",
    "RateLimited",
]
