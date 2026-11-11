import pytest
from ai_pipeline.draft import pick_recipients, recipient_warning


class TestPickRecipients:
    def test_normal_reply_to_from_address(self):
        thread = {
            "messages": [
                {
                    "sender": "boss@company.com",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]

    def test_reply_to_different_from_from_wins(self):
        thread = {
            "messages": [
                {
                    "sender": "boss@company.com",
                    "to": "nikhil@example.com",
                    "reply_to": "replies@company.com",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["replies@company.com"]

    def test_last_message_from_me_reply_to_original_to(self):
        thread = {
            "messages": [
                {
                    "sender": "boss@company.com",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                },
                {
                    "sender": "nikhil@example.com",
                    "to": "boss@company.com",
                    "reply_to": "",
                    "is_from_me": True
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]

    def test_noreply_sender_produces_warning(self):
        thread = {
            "messages": [
                {
                    "sender": "noreply@system.com",
                    "to": "nikhil@example.com",
                    "list_unsubscribe": "",
                    "is_from_me": False
                }
            ]
        }
        
        warning = recipient_warning(thread)
        assert warning == "this sender probably does not read replies"

    def test_no_reply_sender_produces_warning(self):
        thread = {
            "messages": [
                {
                    "sender": "no-reply@service.com",
                    "to": "nikhil@example.com",
                    "list_unsubscribe": "",
                    "is_from_me": False
                }
            ]
        }
        
        warning = recipient_warning(thread)
        assert warning == "this sender probably does not read replies"

    def test_donotreply_sender_produces_warning(self):
        thread = {
            "messages": [
                {
                    "sender": "donotreply@app.com",
                    "to": "nikhil@example.com",
                    "list_unsubscribe": "",
                    "is_from_me": False
                }
            ]
        }
        
        warning = recipient_warning(thread)
        assert warning == "this sender probably does not read replies"

    def test_list_unsubscribe_produces_warning(self):
        thread = {
            "messages": [
                {
                    "sender": "newsletter@news.com",
                    "to": "nikhil@example.com",
                    "list_unsubscribe": "<https://news.com/unsub>",
                    "is_from_me": False
                }
            ]
        }
        
        warning = recipient_warning(thread)
        assert warning == "this sender probably does not read replies"

    def test_normal_sender_produces_no_warning(self):
        thread = {
            "messages": [
                {
                    "sender": "friend@example.com",
                    "to": "nikhil@example.com",
                    "list_unsubscribe": "",
                    "is_from_me": False
                }
            ]
        }
        
        warning = recipient_warning(thread)
        assert warning is None

    def test_mixed_case_addresses_collapse_to_lowercase(self):
        thread = {
            "messages": [
                {
                    "sender": "Boss@COMPANY.COM",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]

    def test_duplicate_addresses_deduplicate(self):
        thread = {
            "messages": [
                {
                    "sender": "boss@company.com, boss@company.com",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]

    def test_display_name_format_resolved_to_bare_address(self):
        thread = {
            "messages": [
                {
                    "sender": '"Boss Man" <boss@company.com>',
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]

    def test_own_address_never_in_result(self):
        thread = {
            "messages": [
                {
                    "sender": "nikhil@example.com",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == []

    def test_empty_addresses_dropped(self):
        thread = {
            "messages": [
                {
                    "sender": "boss@company.com, , ",
                    "to": "nikhil@example.com",
                    "reply_to": "",
                    "is_from_me": False
                }
            ]
        }
        
        result = pick_recipients(thread, "nikhil@example.com")
        assert result == ["boss@company.com"]
