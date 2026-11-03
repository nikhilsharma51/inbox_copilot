"""
Tests for FakeBackend implementation.

Tests verify the fake backend works correctly and matches the interface.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_pipeline.mcp_server.backend.base import (
    Message,
    NotFound,
    Thread,
    ThreadSummary,
)
from ai_pipeline.mcp_server.backend.fake import FakeBackend


@pytest.mark.asyncio
async def test_fake_backend_init_from_fixtures():
    """Test loading fixtures from threads.json"""
    backend = FakeBackend()
    
    # Should have loaded threads
    assert len(backend.threads) > 0
    assert isinstance(backend.threads, dict)
    
    # All should be Thread objects
    for thread_id, thread in backend.threads.items():
        assert isinstance(thread, Thread)
        assert thread.id == thread_id
        assert len(thread.messages) > 0
    
    # Drafts should be empty
    assert len(backend.drafts) == 0
    assert len(backend.sent_drafts) == 0


@pytest.mark.asyncio
async def test_fake_backend_init_with_custom_threads():
    """Test providing custom threads dict"""
    # Create custom thread
    custom_message = Message(
        id="msg_001",
        rfc822_message_id="<msg-001@example.com>",
        sender="test@example.com",
        to=["recipient@example.com"],
        cc=[],
        date=datetime.now(timezone.utc),
        body_text="Test message",
        is_from_me=False
    )
    
    custom_thread = Thread(
        id="thread_custom_001",
        subject="Custom Test Thread",
        messages=[custom_message],
        truncated=False
    )
    
    custom_threads = {"thread_custom_001": custom_thread}
    
    # Initialize with custom threads
    backend = FakeBackend(threads=custom_threads)
    
    # Should use custom threads, not fixtures
    assert len(backend.threads) == 1
    assert backend.threads["thread_custom_001"] == custom_thread


@pytest.mark.asyncio
async def test_list_threads_all():
    """Test listing all threads without query"""
    backend = FakeBackend()
    
    results, next_token = await backend.list_threads("", max_results=10)
    
    # Should return ThreadSummary objects
    assert len(results) > 0
    assert all(isinstance(r, ThreadSummary) for r in results)
    
    # Check fields are populated
    for summary in results:
        assert summary.id
        assert summary.subject
        assert summary.message_count > 0
        assert summary.last_message_id


@pytest.mark.asyncio
async def test_list_threads_with_query():
    """Test listing threads with search query"""
    backend = FakeBackend()
    
    # Search for internship-related emails
    results, _ = await backend.list_threads("internship", max_results=10)
    
    # Should find matches
    assert len(results) > 0
    
    # All results should match query (case-insensitive)
    for summary in results:
        combined_text = (
            summary.subject + " " +
            " ".join(msg.body_text for msg in backend.threads[summary.id].messages)
        ).lower()
        assert "internship" in combined_text


@pytest.mark.asyncio
async def test_list_threads_pagination():
    """Test pagination of thread list"""
    backend = FakeBackend()
    
    # First page
    results1, next_token = await backend.list_threads("", max_results=5)
    assert len(results1) <= 5
    
    # If there's a next page
    if next_token:
        results2, _ = await backend.list_threads("", max_results=5, page_token=next_token)
        assert len(results2) > 0
        
        # IDs should be different
        ids1 = {r.id for r in results1}
        ids2 = {r.id for r in results2}
        assert len(ids1 & ids2) == 0  # No overlap


@pytest.mark.asyncio
async def test_list_threads_max_results_clamped():
    """Test that max_results is clamped to 1-25"""
    backend = FakeBackend()
    
    # Request more than 25
    results, _ = await backend.list_threads("", max_results=1000)
    assert len(results) <= 25
    
    # Request 0 (should be clamped to 1)
    results, _ = await backend.list_threads("", max_results=0)
    assert len(results) <= 1


@pytest.mark.asyncio
async def test_get_thread_success():
    """Test getting a thread by ID"""
    backend = FakeBackend()
    
    # Get first thread
    thread_id = list(backend.threads.keys())[0]
    thread = await backend.get_thread(thread_id)
    
    # Should return full thread
    assert isinstance(thread, Thread)
    assert thread.id == thread_id
    assert len(thread.messages) > 0


@pytest.mark.asyncio
async def test_get_thread_not_found():
    """Test getting a non-existent thread"""
    backend = FakeBackend()
    
    # Try to get non-existent thread
    with pytest.raises(NotFound) as exc_info:
        await backend.get_thread("thread_does_not_exist")
    
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_draft_success():
    """Test creating a draft"""
    backend = FakeBackend()
    
    # Get first thread
    thread_id = list(backend.threads.keys())[0]
    
    # Create draft
    draft = await backend.create_draft(
        thread_id=thread_id,
        body="This is my reply",
        subject="Re: Original Subject",
        to=["recipient@example.com"],
        cc=[]
    )
    
    # Should be stored
    assert draft.id in backend.drafts
    assert draft.thread_id == thread_id
    assert draft.body == "This is my reply"
    assert draft.subject == "Re: Original Subject"


@pytest.mark.asyncio
async def test_create_draft_auto_recipient():
    """Test creating draft with auto-detected recipient"""
    backend = FakeBackend()
    
    thread_id = list(backend.threads.keys())[0]
    thread = backend.threads[thread_id]
    last_message = thread.messages[-1]
    
    # Create draft without specifying recipient
    draft = await backend.create_draft(
        thread_id=thread_id,
        body="Reply",
    )
    
    # Should default to last sender
    assert last_message.sender in draft.to


@pytest.mark.asyncio
async def test_create_draft_auto_subject():
    """Test creating draft with auto-generated subject"""
    backend = FakeBackend()
    
    thread_id = list(backend.threads.keys())[0]
    thread = backend.threads[thread_id]
    
    # Create draft without specifying subject
    draft = await backend.create_draft(
        thread_id=thread_id,
        body="Reply",
    )
    
    # Should have Re: prefix
    assert draft.subject.startswith("Re:")
    assert thread.subject in draft.subject


@pytest.mark.asyncio
async def test_create_draft_thread_not_found():
    """Test creating draft in non-existent thread"""
    backend = FakeBackend()
    
    with pytest.raises(NotFound):
        await backend.create_draft(
            thread_id="thread_does_not_exist",
            body="reply",
        )


@pytest.mark.asyncio
async def test_get_draft_success():
    """Test getting a draft"""
    backend = FakeBackend()
    
    # Create draft first
    thread_id = list(backend.threads.keys())[0]
    draft = await backend.create_draft(thread_id, body="test")
    
    # Get draft
    retrieved = await backend.get_draft(draft.id)
    
    assert retrieved.id == draft.id
    assert retrieved.body == "test"


@pytest.mark.asyncio
async def test_get_draft_not_found():
    """Test getting non-existent draft"""
    backend = FakeBackend()
    
    with pytest.raises(NotFound):
        await backend.get_draft("draft_does_not_exist")


@pytest.mark.asyncio
async def test_send_draft_success():
    """Test sending a draft"""
    backend = FakeBackend()
    
    # Create draft
    thread_id = list(backend.threads.keys())[0]
    draft = await backend.create_draft(thread_id, body="test")
    draft_id = draft.id
    
    # Send draft
    message_id = await backend.send_draft(draft_id)
    
    # Should be moved to sent and removed from drafts
    assert message_id == draft_id
    assert draft_id not in backend.drafts
    assert draft_id in backend.sent_drafts


@pytest.mark.asyncio
async def test_send_draft_not_found():
    """Test sending non-existent draft"""
    backend = FakeBackend()
    
    with pytest.raises(NotFound):
        await backend.send_draft("draft_does_not_exist")


@pytest.mark.asyncio
async def test_send_draft_already_sent():
    """Test sending a draft that's already been sent"""
    backend = FakeBackend()
    
    # Create and send draft
    thread_id = list(backend.threads.keys())[0]
    draft = await backend.create_draft(thread_id, body="test")
    draft_id = draft.id
    
    await backend.send_draft(draft_id)
    
    # Try to send again
    with pytest.raises(NotFound) as exc_info:
        await backend.send_draft(draft_id)
    
    assert "already been sent" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_sent_draft():
    """Test that sent drafts cannot be retrieved"""
    backend = FakeBackend()
    
    # Create and send draft
    thread_id = list(backend.threads.keys())[0]
    draft = await backend.create_draft(thread_id, body="test")
    draft_id = draft.id
    
    await backend.send_draft(draft_id)
    
    # Try to get sent draft
    with pytest.raises(NotFound) as exc_info:
        await backend.get_draft(draft_id)
    
    assert "already been sent" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
