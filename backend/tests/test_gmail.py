import base64
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.gmail import GmailClient, get_valid_access_token, ReconnectNeeded
from app.db import User
from app.auth import encrypt_token


@pytest.fixture
def mock_service():
    return MagicMock()


@pytest.fixture
def gmail_client():
    return GmailClient(access_token="test_access_token")


class TestListThreads:
    def test_list_threads_sequential_calls(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            list_return = MagicMock()
            list_return.execute.return_value = {
                "threads": [
                    {"id": "thread1", "snippet": "Hello world"},
                    {"id": "thread2", "snippet": "Test &amp; verify"},
                ]
            }
            mock_service.users().threads().list.return_value = list_return
            
            get_return = MagicMock()
            get_return.execute.side_effect = [
                {
                    "messages": [{
                        "payload": {
                            "headers": [
                                {"name": "Subject", "value": "Test 1"},
                                {"name": "From", "value": "sender@example.com"},
                                {"name": "Date", "value": "Mon, 1 Jan 2024 10:00:00 +0000"},
                                {"name": "Message-ID", "value": "<msg1@example.com>"},
                            ]
                        }
                    }]
                },
                {
                    "messages": [{
                        "payload": {
                            "headers": [
                                {"name": "Subject", "value": "Test 2"},
                                {"name": "From", "value": "other@example.com"},
                                {"name": "Date", "value": "Tue, 2 Jan 2024 10:00:00 +0000"},
                                {"name": "Message-ID", "value": "<msg2@example.com>"},
                            ]
                        }
                    }]
                },
            ]
            mock_service.users().threads().get.return_value = get_return
            
            result = gmail_client.list_threads()
            
            assert len(result) == 2
            assert result[0]["thread_id"] == "thread1"
            assert result[0]["subject"] == "Test 1"
            assert result[1]["snippet"] == "Test & verify"
            
            assert get_return.execute.call_count == 2


class TestGetThread:
    def test_get_thread_multipart_text_plain(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Test"},
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "To", "value": "me@example.com"},
                            {"name": "Message-ID", "value": "<msg@example.com>"},
                        ],
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {
                                    "data": base64.urlsafe_b64encode(b"Hello, this is plain text").decode().rstrip("=")
                                }
                            }
                        ]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1", user_email="me@example.com")
            
            assert result["subject"] == "Test"
            assert len(result["messages"]) == 1
            assert result["messages"][0]["body"] == "Hello, this is plain text"
            assert result["messages"][0]["is_from_me"] is False

    def test_get_thread_html_fallback_to_text(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            html_content = "<html><body><p>Hello HTML</p></body></html>"
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "HTML Test"},
                            {"name": "From", "value": "sender@example.com"},
                        ],
                        "parts": [
                            {
                                "mimeType": "text/html",
                                "body": {
                                    "data": base64.urlsafe_b64encode(html_content.encode()).decode().rstrip("=")
                                }
                            }
                        ]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1")
            
            assert "Hello HTML" in result["messages"][0]["body"]

    def test_get_thread_base64url_padding(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            text = "a"
            encoded_no_padding = base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [{"name": "Subject", "value": "Padding Test"}],
                        "parts": [{
                            "mimeType": "text/plain",
                            "body": {"data": encoded_no_padding}
                        }]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1")
            assert result["messages"][0]["body"] == "a"

    def test_get_thread_case_insensitive_headers(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [
                            {"name": "subject", "value": "lowercase subject"},
                            {"name": "FROM", "value": "sender@example.com"},
                            {"name": "Message-ID", "value": "<msg@example.com>"},
                        ],
                        "parts": [{
                            "mimeType": "text/plain",
                            "body": {"data": base64.urlsafe_b64encode(b"test").decode().rstrip("=")}
                        }]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1")
            assert result["subject"] == "lowercase subject"

    def test_get_thread_skip_attachments(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [{"name": "Subject", "value": "With Attachment"}],
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {"data": base64.urlsafe_b64encode(b"Email body").decode().rstrip("=")}
                            },
                            {
                                "mimeType": "application/pdf",
                                "filename": "document.pdf",
                                "body": {}
                            }
                        ]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1")
            assert result["messages"][0]["body"] == "Email body"

    def test_get_thread_internal_date_conversion(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [{"name": "Subject", "value": "Date Test"}],
                        "parts": [{
                            "mimeType": "text/plain",
                            "body": {"data": base64.urlsafe_b64encode(b"test").decode().rstrip("=")}
                        }]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1")
            date_obj = result["messages"][0]["date"]
            
            assert isinstance(date_obj, datetime)
            assert date_obj.tzinfo == timezone.utc
            assert date_obj.year == 2024

    def test_get_thread_is_from_me(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "internalDate": "1704110400000",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "From Me"},
                            {"name": "From", "value": "me@example.com"},
                        ],
                        "parts": [{
                            "mimeType": "text/plain",
                            "body": {"data": base64.urlsafe_b64encode(b"test").decode().rstrip("=")}
                        }]
                    }
                }]
            }
            
            result = gmail_client.get_thread("thread1", user_email="me@example.com")
            assert result["messages"][0]["is_from_me"] is True


class TestSnippetUnescaping:
    def test_snippet_html_entity_unescaping(self, gmail_client, mock_service):
        with patch("app.gmail.build") as mock_build:
            mock_build.return_value = mock_service
            
            mock_service.users().threads().list().execute.return_value = {
                "threads": [
                    {"id": "thread1", "snippet": "Don&#39;t forget &amp; remember"}
                ]
            }
            
            mock_service.users().threads().get().execute.return_value = {
                "messages": [{
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Test"},
                            {"name": "From", "value": "sender@example.com"},
                        ]
                    }
                }]
            }
            
            result = gmail_client.list_threads()
            assert result[0]["snippet"] == "Don't forget & remember"


class TestGetValidAccessToken:
    def test_get_valid_access_token_success(self):
        with patch("app.gmail.decrypt_token") as mock_decrypt:
            with patch("app.gmail.Credentials") as mock_creds_class:
                mock_decrypt.return_value = "test_refresh_token"
                mock_creds = MagicMock()
                mock_creds.token = "new_access_token"
                mock_creds_class.return_value = mock_creds
                
                user = MagicMock()
                user.refresh_token_enc = "encrypted_token"
                
                result = get_valid_access_token(user)
                
                assert result == "new_access_token"
                mock_creds.refresh.assert_called_once()

    def test_get_valid_access_token_no_refresh_token(self):
        user = MagicMock()
        user.refresh_token_enc = None
        
        with pytest.raises(ReconnectNeeded):
            get_valid_access_token(user)

    def test_get_valid_access_token_decrypt_error(self):
        from app.auth import TokenDecryptError
        
        with patch("app.gmail.decrypt_token") as mock_decrypt:
            mock_decrypt.side_effect = TokenDecryptError("Decrypt error")
            
            user = MagicMock()
            user.refresh_token_enc = "encrypted_token"
            
            with pytest.raises(ReconnectNeeded):
                get_valid_access_token(user)

    def test_get_valid_access_token_invalid_grant(self):
        with patch("app.gmail.decrypt_token") as mock_decrypt:
            with patch("app.gmail.Credentials") as mock_creds_class:
                mock_decrypt.return_value = "test_refresh_token"
                mock_creds = MagicMock()
                mock_creds.refresh.side_effect = Exception("invalid_grant: The user must authenticate.")
                mock_creds_class.return_value = mock_creds
                
                user = MagicMock()
                user.refresh_token_enc = "encrypted_token"
                
                with pytest.raises(ReconnectNeeded):
                    get_valid_access_token(user)
