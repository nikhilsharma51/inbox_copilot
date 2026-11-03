from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str
    rfc822_message_id: str
    sender: str
    to: List[str]
    cc: List[str]
    date: datetime
    body_text: str
    is_from_me: bool


class ThreadSummary(BaseModel):
    id: str
    subject: str
    snippet: str
    participants: List[str]
    last_message_at: datetime
    message_count: int
    last_message_id: str


class Thread(BaseModel):
    id: str
    subject: str
    messages: List[Message]
    truncated: bool = False


class DraftIn(BaseModel):
    thread_id: str
    subject: str
    body: str
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None


class Draft(BaseModel):
    id: str
    thread_id: str
    subject: str
    body: str
    to: List[str]
    cc: List[str]


class BackendError(Exception):
    pass


class NotFound(BackendError):
    pass


class AuthExpired(BackendError):
    pass


class RateLimited(BackendError):
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")


class MailBackend(ABC):

    @abstractmethod
    async def list_threads(
        self,
        query: str,
        max_results: int = 20,
        page_token: Optional[str] = None
    ) -> tuple[List[ThreadSummary], Optional[str]]:
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> Thread:
        pass

    @abstractmethod
    async def create_draft(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None,
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None
    ) -> Draft:
        pass

    @abstractmethod
    async def get_draft(self, draft_id: str) -> Draft:
        pass

    @abstractmethod
    async def send_draft(self, draft_id: str) -> None:
        pass