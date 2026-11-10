import base64
import html
import json
from datetime import datetime, timezone
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from app.auth import decrypt_token, TokenDecryptError
from app.config import settings
from app.db import User

logger = logging.getLogger(__name__)


class ReconnectNeeded(Exception):
    pass


class GmailClient:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def list_threads(self, query: str = "newer_than:30d", max_results: int = 100):
        service = build("gmail", "v1", credentials=Credentials(token=self.access_token), cache_discovery=False)
        
        results = service.users().threads().list(userId="me", q=query, maxResults=min(max_results, 100)).execute()
        threads_data = results.get("threads", [])
        
        logger.info(f"Found {len(threads_data)} threads")
        
        output = []
        for thread in threads_data:
            thread_id = thread["id"]
            snippet = thread.get("snippet", "")
            
            metadata_result = service.users().threads().get(
                userId="me",
                id=thread_id,
                format="metadata",
                metadataHeaders=["Subject", "From", "To", "Date", "Message-ID"]
            ).execute()
            
            headers = self._extract_headers(metadata_result.get("messages", [{}])[0])
            subject = headers.get("subject", "")
            sender = headers.get("from", "")
            date_str = headers.get("date", "")
            last_message_id = headers.get("message-id", "")
            
            snippet_unescaped = html.unescape(snippet)
            
            output.append({
                "thread_id": thread_id,
                "subject": subject,
                "sender": sender,
                "snippet": snippet_unescaped,
                "date": date_str,
                "last_message_id": last_message_id,
            })
        
        return output

    def get_thread(self, thread_id: str, user_email: str = None):
        service = build("gmail", "v1", credentials=Credentials(token=self.access_token), cache_discovery=False)
        
        result = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        
        subject = ""
        messages = []
        
        for message in result.get("messages", []):
            headers = self._extract_headers(message)
            subject = headers.get("subject", subject)
            
            internal_date_ms = int(message.get("internalDate", 0))
            date = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)
            
            sender = headers.get("from", "")
            to = headers.get("to", "")
            cc = headers.get("cc", "")
            message_id = headers.get("message-id", "")
            
            body_text = self._extract_body(message.get("payload", {}))
            
            is_from_me = False
            if user_email and sender:
                is_from_me = user_email.lower() in sender.lower()
            
            messages.append({
                "sender": sender,
                "to": to,
                "cc": cc,
                "date": date,
                "message_id": message_id,
                "body": body_text,
                "is_from_me": is_from_me,
            })
        
        logger.info(f"Retrieved thread {thread_id} with {len(messages)} messages")
        
        return {
            "subject": subject,
            "messages": messages,
        }

    def send_reply(self, thread_id: str, to: str, subject: str, body: str, in_reply_to: str = None, references: str = None):
        service = build("gmail", "v1", credentials=Credentials(token=self.access_token), cache_discovery=False)
        
        message_text = f"Subject: {subject}\r\n"
        if references:
            message_text += f"References: {references}\r\n"
        if in_reply_to:
            message_text += f"In-Reply-To: {in_reply_to}\r\n"
        message_text += f"To: {to}\r\n\r\n{body}"
        
        message_bytes = message_text.encode("utf-8")
        message_b64 = base64.urlsafe_b64encode(message_bytes).decode("utf-8").rstrip("=")
        
        send_message = {
            "raw": message_b64,
            "threadId": thread_id,
        }
        
        service.users().messages().send(userId="me", body=send_message).execute()
        
        logger.info(f"Sent reply in thread {thread_id}")

    def _extract_headers(self, message: dict) -> dict:
        headers_list = message.get("payload", {}).get("headers", [])
        headers = {}
        for h in headers_list:
            name_lower = h.get("name", "").lower()
            headers[name_lower] = h.get("value", "")
        return headers

    def _extract_body(self, payload: dict) -> str:
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/plain":
                    return self._decode_part(part)
            
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                if mime_type == "text/html":
                    html_content = self._decode_part(part)
                    soup = BeautifulSoup(html_content, "html.parser")
                    return soup.get_text()
        
        if payload.get("mimeType", "").startswith("text/"):
            return self._decode_part(payload)
        
        return ""

    def _decode_part(self, part: dict) -> str:
        data = part.get("body", {}).get("data", "")
        if not data:
            return ""
        
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += "=" * padding
        
        try:
            decoded = base64.urlsafe_b64decode(data)
            return decoded.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def get_valid_access_token(user: User) -> str:
    if not user.refresh_token_enc:
        raise ReconnectNeeded("No refresh token available")
    
    try:
        refresh_token = decrypt_token(user.refresh_token_enc)
    except TokenDecryptError as e:
        raise ReconnectNeeded(f"Failed to decrypt refresh token: {e}") from e
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    
    try:
        creds.refresh(Request())
    except Exception as e:
        if "invalid_grant" in str(e).lower():
            raise ReconnectNeeded("Refresh token expired or revoked") from e
        raise
    
    return creds.token


class FakeGmail:
    def __init__(self):
        fixtures_path = Path(__file__).parent.parent / "data" / "fixtures.json"
        with open(fixtures_path) as f:
            self.data = json.load(f)
        self.sent = []
        self.thread_map = {t["thread_id"]: t for t in self.data["threads"]}

    def list_threads(self, query: str = "newer_than:30d", max_results: int = 100):
        threads = self.data["threads"][:max_results]
        
        output = []
        for thread in threads:
            first_message = thread["messages"][0]
            snippet = first_message["body"][:100]
            snippet_unescaped = html.unescape(snippet)
            
            output.append({
                "thread_id": thread["thread_id"],
                "subject": thread["subject"],
                "sender": first_message["sender"],
                "snippet": snippet_unescaped,
                "date": first_message["date"],
                "last_message_id": thread["messages"][-1]["message_id"],
            })
        
        logger.info(f"Found {len(threads)} threads")
        return output

    def get_thread(self, thread_id: str, user_email: str = None):
        thread = self.thread_map.get(thread_id)
        if not thread:
            return {"subject": "", "messages": []}
        
        messages = []
        for msg in thread["messages"]:
            is_from_me = False
            if user_email:
                is_from_me = user_email.lower() in msg["sender"].lower()
            
            date_obj = datetime.fromisoformat(msg["date"])
            
            messages.append({
                "sender": msg["sender"],
                "to": msg["to"],
                "cc": msg["cc"],
                "date": date_obj,
                "message_id": msg["message_id"],
                "body": msg["body"],
                "is_from_me": is_from_me,
            })
        
        logger.info(f"Retrieved thread {thread_id} with {len(messages)} messages")
        
        return {
            "subject": thread["subject"],
            "messages": messages,
        }

    def send_reply(self, thread_id: str, to: str, subject: str, body: str, in_reply_to: str = None, references: str = None):
        self.sent.append({
            "thread_id": thread_id,
            "to": to,
            "subject": subject,
            "body": body,
            "in_reply_to": in_reply_to,
            "references": references,
        })
        
        logger.info(f"Sent reply in thread {thread_id}")


def get_mailbox(user: User):
    if settings.mailbox_mode == "fake":
        return FakeGmail()
    else:
        access_token = get_valid_access_token(user)
        return GmailClient(access_token=access_token)
