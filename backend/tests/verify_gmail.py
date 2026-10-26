
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent.parent 
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def verify_gmail() -> None:
    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if not credentials.refresh_token:
        raise RuntimeError("No refresh token found in token.json")

    credentials.refresh(Request())

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    print("Access token refreshed successfully.")

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    profile = gmail.users().getProfile(userId="me").execute()

    print("Gmail API call successful.")
    print("Messages in mailbox:", profile.get("messagesTotal"))
    print("Threads in mailbox:", profile.get("threadsTotal"))


if __name__ == "__main__":
    verify_gmail()
