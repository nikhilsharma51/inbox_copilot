import inspect
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.gmail import FakeGmail, GmailClient, get_mailbox, ReconnectNeeded
from app.db import User


@pytest.fixture
def fake_gmail():
    return FakeGmail()


@pytest.fixture
def fixtures():
    fixtures_path = Path(__file__).parent.parent / "data" / "fixtures.json"
    with open(fixtures_path) as f:
        return json.load(f)


class TestFixturesLoad:
    def test_fixtures_load_successfully(self, fixtures):
        assert "threads" in fixtures
        assert len(fixtures["threads"]) > 0

    def test_fixtures_structure(self, fixtures):
        for thread in fixtures["threads"]:
            assert "thread_id" in thread
            assert "subject" in thread
            assert "messages" in thread
            assert len(thread["messages"]) > 0
            
            for msg in thread["messages"]:
                assert "sender" in msg
                assert "to" in msg
                assert "cc" in msg
                assert "date" in msg
                assert "message_id" in msg
                assert "body" in msg
                assert "is_from_me" in msg


class TestFakeGmailListThreads:
    def test_list_threads_returns_correct_shape(self, fake_gmail):
        result = fake_gmail.list_threads()
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        for thread in result:
            assert "thread_id" in thread
            assert "subject" in thread
            assert "sender" in thread
            assert "snippet" in thread
            assert "date" in thread
            assert "last_message_id" in thread

    def test_list_threads_respects_max_results(self, fake_gmail):
        result = fake_gmail.list_threads(max_results=5)
        assert len(result) == 5

    def test_list_threads_default_max_results(self, fake_gmail, fixtures):
        result = fake_gmail.list_threads()
        assert len(result) == min(len(fixtures["threads"]), 100)


class TestFakeGmailGetThread:
    def test_get_thread_returns_correct_shape(self, fake_gmail):
        result = fake_gmail.get_thread("thread_internship")
        
        assert "subject" in result
        assert "messages" in result
        assert isinstance(result["messages"], list)
        
        for msg in result["messages"]:
            assert "sender" in msg
            assert "to" in msg
            assert "cc" in msg
            assert "date" in msg
            assert "message_id" in msg
            assert "body" in msg
            assert "is_from_me" in msg

    def test_get_thread_is_from_me_true(self, fake_gmail):
        result = fake_gmail.get_thread("thread_my_sent", user_email="nikhil@example.com")
        
        has_from_me = any(msg["is_from_me"] for msg in result["messages"])
        assert has_from_me is True

    def test_get_thread_html_only_has_body(self, fake_gmail):
        result = fake_gmail.get_thread("thread_html_only")
        
        assert len(result["messages"]) > 0
        assert len(result["messages"][0]["body"]) > 0

    def test_get_thread_injection_emails_present(self, fake_gmail):
        injection_threads = [
            "thread_injection1",
            "thread_injection2",
            "thread_injection3",
            "thread_injection4",
            "thread_injection5",
        ]
        
        for thread_id in injection_threads:
            result = fake_gmail.get_thread(thread_id)
            assert result["subject"] != ""
            assert len(result["messages"]) > 0


class TestFakeGmailSendReply:
    def test_send_reply_appends_to_sent(self, fake_gmail):
        fake_gmail.send_reply(
            thread_id="thread1",
            to="recipient@example.com",
            subject="Re: Test",
            body="Reply body"
        )
        
        assert len(fake_gmail.sent) == 1
        assert fake_gmail.sent[0]["thread_id"] == "thread1"
        assert fake_gmail.sent[0]["to"] == "recipient@example.com"

    def test_send_reply_multiple(self, fake_gmail):
        for i in range(3):
            fake_gmail.send_reply(
                thread_id=f"thread{i}",
                to=f"user{i}@example.com",
                subject=f"Re: Test {i}",
                body=f"Body {i}"
            )
        
        assert len(fake_gmail.sent) == 3


class TestGetMailbox:
    def test_get_mailbox_returns_fake_gmail_when_fake_mode(self):
        with patch("app.gmail.settings.mailbox_mode", "fake"):
            user = MagicMock()
            result = get_mailbox(user)
            
            assert isinstance(result, FakeGmail)

    def test_get_mailbox_returns_gmail_client_when_gmail_mode(self):
        with patch("app.gmail.settings.mailbox_mode", "gmail"):
            with patch("app.gmail.get_valid_access_token") as mock_get_token:
                mock_get_token.return_value = "test_token"
                
                user = MagicMock()
                user.refresh_token_enc = "encrypted_token"
                
                with patch("app.gmail.build"):
                    result = get_mailbox(user)
                    assert isinstance(result, GmailClient)

    def test_get_mailbox_propagates_reconnect_needed(self):
        with patch("app.gmail.settings.mailbox_mode", "gmail"):
            with patch("app.gmail.get_valid_access_token") as mock_get_token:
                mock_get_token.side_effect = ReconnectNeeded("No refresh token")
                
                user = MagicMock()
                
                with pytest.raises(ReconnectNeeded):
                    get_mailbox(user)


class TestMethodSignatures:
    def test_fake_gmail_and_gmail_client_have_same_methods(self):
        fake_methods = set(
            name for name, _ in inspect.getmembers(FakeGmail, predicate=inspect.isfunction)
            if not name.startswith("_")
        )
        
        gmail_methods = set(
            name for name, _ in inspect.getmembers(GmailClient, predicate=inspect.isfunction)
            if not name.startswith("_")
        )
        
        public_methods = {"list_threads", "get_thread", "send_reply"}
        
        for method in public_methods:
            assert method in fake_methods
            assert method in gmail_methods

    def test_method_signatures_match(self):
        fake_list_sig = inspect.signature(FakeGmail.list_threads)
        gmail_list_sig = inspect.signature(GmailClient.list_threads)
        
        assert str(fake_list_sig) == str(gmail_list_sig)
        
        fake_get_sig = inspect.signature(FakeGmail.get_thread)
        gmail_get_sig = inspect.signature(GmailClient.get_thread)
        
        assert str(fake_get_sig) == str(gmail_get_sig)
