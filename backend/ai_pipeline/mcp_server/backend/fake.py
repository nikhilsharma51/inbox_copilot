"""
Fake Backend implementation for testing.

This backend loads test emails from fixtures and provides an in-memory
implementation of the MailBackend interface for testing purposes.
"""

import json
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .base import (
    AuthExpired,
    Draft,
    MailBackend,
    NotFound,
    RateLimited,
    Thread,
    ThreadSummary,
)


class FakeBackend(MailBackend):
    """
    In-memory Mail backend for testing.
    
    Loads test emails from fixtures/threads.json on initialization.
    Drafts are stored in-memory; sending moves them to a sent set.
    """

    def __init__(self, threads: Optional[dict] = None) -> None:
        """
        Initialize FakeBackend.
        
        Args:
            threads: Optional dict of pre-loaded Thread objects.
                    If None, loads from fixtures/threads.json.
        """
        # If threads provided, use them. Otherwise load from fixtures.
        if threads is not None:
            self.threads = threads
        else:
            # Load from JSON fixtures
            file_path = Path(__file__).parent.parent / "fixtures" / "threads.json"
            
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # Validate and store threads
            self.threads = {}
            for thread_data in data:
                thread = Thread.model_validate(thread_data)
                self.threads[thread.id] = thread
        
        # Draft storage
        self.drafts = {}          # {draft_id -> Draft}
        self.sent_drafts = set()  # Set of draft IDs that have been sent

    async def list_threads(
        self,
        query: str,
        max_results: int = 20,
        page_token: Optional[str] = None
    ) -> tuple[List[ThreadSummary], Optional[str]]:
        """
        List threads matching the query.
        
        Args:
            query: Search query (case-insensitive, searches subject + body)
            max_results: Max threads to return (clamped to 1-25)
            page_token: Pagination token (integer as string)
        
        Returns:
            Tuple of (results, next_page_token)
        """
        # Clamp max_results to valid range
        max_results = max(1, min(max_results, 25))

        matching_threads = []

        # Search threads
        for thread in self.threads.values():
            if not thread.messages:
                continue

            # Search in subject and all message bodies
            search_text = (
                thread.subject + " " +
                " ".join(
                    message.body_text
                    for message in thread.messages
                )
            ).lower()

            # Skip if query doesn't match
            if query and query.lower() not in search_text:
                continue

            # Build summary from last message
            last_message = thread.messages[-1]

            matching_threads.append(
                ThreadSummary(
                    id=thread.id,
                    subject=thread.subject,
                    snippet=last_message.body_text[:100],
                    participants=list(set(
                        message.sender
                        for message in thread.messages
                    )),
                    last_message_at=last_message.date,
                    message_count=len(thread.messages),
                    last_message_id=last_message.id
                )
            )

        # Pagination
        start = int(page_token) if page_token else 0
        results = matching_threads[start:start + max_results]

        # Next page token if more results exist
        next_page_token = (
            str(start + max_results)
            if start + max_results < len(matching_threads)
            else None
        )

        return results, next_page_token

    async def get_thread(self, thread_id: str) -> Thread:
        """
        Get a full thread by ID.
        
        Args:
            thread_id: ID of thread to fetch
        
        Returns:
            Full Thread object with all messages
        
        Raises:
            NotFound: If thread doesn't exist
        """
        thread = self.threads.get(thread_id)

        if thread is None:
            raise NotFound(f"Thread {thread_id} not found")

        return thread

    async def create_draft(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None,
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None
    ) -> Draft:
        """
        Create a draft in a thread.
        
        Args:
            thread_id: ID of thread to reply in
            body: Draft body text
            subject: Draft subject (defaults to "Re: <original>")
            to: Recipients (defaults to last sender)
            cc: CC recipients (defaults to empty)
        
        Returns:
            Created Draft object
        
        Raises:
            NotFound: If thread or last message not found
        """
        thread = self.threads.get(thread_id)

        if thread is None:
            raise NotFound(f"Thread {thread_id} not found")

        if not thread.messages:
            raise NotFound(f"Thread {thread_id} has no messages")

        # Generate draft ID
        draft_id = str(uuid4())

        # Get sender of last message (for default recipient)
        original_message = thread.messages[-1]

        # Create draft
        draft = Draft(
            id=draft_id,
            thread_id=thread_id,
            subject=subject or f"Re: {thread.subject}",
            body=body,
            to=to if to is not None else [original_message.sender],
            cc=cc if cc is not None else []
        )

        # Store draft
        self.drafts[draft_id] = draft

        return draft

    async def get_draft(self, draft_id: str) -> Draft:
        """
        Get a draft by ID.
        
        Args:
            draft_id: ID of draft to fetch
        
        Returns:
            Draft object
        
        Raises:
            NotFound: If draft not found or already sent
        """
        # Check if already sent
        if draft_id in self.sent_drafts:
            raise NotFound(f"Draft {draft_id} has already been sent")

        # Get draft
        draft = self.drafts.get(draft_id)

        if draft is None:
            raise NotFound(f"Draft {draft_id} not found")

        return draft

    async def send_draft(self, draft_id: str) -> str:
        """
        Send a draft (move from drafts to sent).
        
        Args:
            draft_id: ID of draft to send
        
        Returns:
            Message ID (same as draft ID in fake backend)
        
        Raises:
            NotFound: If draft not found or already sent
        """
        # Check if already sent
        if draft_id in self.sent_drafts:
            raise NotFound(f"Draft {draft_id} has already been sent")

        # Check if draft exists
        if draft_id not in self.drafts:
            raise NotFound(f"Draft {draft_id} not found")

        # Move draft to sent and remove from drafts (like Gmail does)
        draft = self.drafts.pop(draft_id)
        self.sent_drafts.add(draft_id)

        return draft.id
