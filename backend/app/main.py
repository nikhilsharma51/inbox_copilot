
import json
import os
from pathlib import Path

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent

CLIENT_SECRETS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

REDIRECT_URI = "http://localhost:4000/auth/google/callback"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "dev-only-change-this-session-secret",
)

app = FastAPI(title="Email Copilot API")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,  # Local development only
)


def create_oauth_flow(
    state: str | None = None,
    autogenerate_code_verifier: bool = False,
) -> Flow:
    if not CLIENT_SECRETS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "credentials.json not found. "
                f"Expected location: {CLIENT_SECRETS_FILE}"
            ),
        )

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
        state=state,
        autogenerate_code_verifier=autogenerate_code_verifier,
    )

    flow.redirect_uri = REDIRECT_URI
    return flow


def save_credentials(credentials: Credentials) -> None:
    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )


def get_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected. Visit /auth/google first.",
        )

    try:
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            save_credentials(credentials)

        if not credentials.valid:
            raise HTTPException(
                status_code=401,
                detail="Gmail authorization expired. Visit /auth/google again.",
            )

        return credentials

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Could not load Gmail credentials: {exc}",
        ) from exc


def get_header(headers: list[dict], name: str) -> str | None:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None



@app.get("/")
def home():
    return {
        "app": "Email Copilot API",
        "status": "running",
        "docs": "/docs",
        "connect_gmail": "/auth/google",
        "fetch_emails": "/emails?limit=10",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/google")
def google_login(request: Request):
    # Start a fresh OAuth attempt.
    request.session.clear()

    flow = create_oauth_flow(
        autogenerate_code_verifier=True,
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    # Persist BOTH values across Google's redirect.
    request.session["oauth_state"] = state
    request.session["code_verifier"] = flow.code_verifier

    return RedirectResponse(
        url=authorization_url,
        status_code=302,
    )


@app.get("/auth/google/callback")
def google_callback(request: Request):
 
    google_error = request.query_params.get("error")

    if google_error:
        raise HTTPException(
            status_code=400,
            detail=f"Google authorization failed: {google_error}",
        )

    authorization_code = request.query_params.get("code")
    returned_state = request.query_params.get("state")

    stored_state = request.session.get("oauth_state")
    code_verifier = request.session.get("code_verifier")

    if not authorization_code:
        raise HTTPException(
            status_code=400,
            detail="Google did not return an authorization code.",
        )

    if not stored_state or not returned_state:
        raise HTTPException(
            status_code=400,
            detail="OAuth state is missing. Restart at /auth/google.",
        )

    if stored_state != returned_state:
        request.session.clear()
        raise HTTPException(
            status_code=400,
            detail="OAuth state mismatch. Restart at /auth/google.",
        )

    if not code_verifier:
        request.session.clear()
        raise HTTPException(
            status_code=400,
            detail=(
                "OAuth code verifier is missing. "
                "Restart authentication at /auth/google."
            ),
        )

    try:
        # Restore the original state and PKCE verifier.
        flow = create_oauth_flow(
            state=stored_state,
            autogenerate_code_verifier=False,
        )

        flow.code_verifier = code_verifier

        # Exchange the returned authorization code for tokens.
        flow.fetch_token(
            authorization_response=str(request.url),
        )

        credentials = flow.credentials
        save_credentials(credentials)

        # Remove temporary OAuth values after successful exchange.
        request.session.clear()

        return {
            "status": "success",
            "message": "Gmail connected successfully.",
            "next_step": "/emails?limit=10",
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {exc}",
        ) from exc


@app.get("/emails")
def get_emails(limit: int = 10):
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    credentials = get_credentials()

    try:
        gmail = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        response = (
            gmail.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=limit,
            )
            .execute()
        )

        messages = response.get("messages", [])
        emails = []

        for message in messages:
            details = (
                gmail.users()
                .messages()
                .get(
                    userId="me",
                    id=message["id"],
                    format="metadata",
                    metadataHeaders=[
                        "From",
                        "To",
                        "Cc",
                        "Subject",
                        "Date",
                    ],
                )
                .execute()
            )

            payload = details.get("payload", {})
            headers = payload.get("headers", [])

            emails.append({
                "id": details["id"],
                "thread_id": details.get("threadId"),
                "from": get_header(headers, "From"),
                "to": get_header(headers, "To"),
                "cc": get_header(headers, "Cc"),
                "subject": get_header(headers, "Subject"),
                "date": get_header(headers, "Date"),
                "snippet": details.get("snippet", ""),
                "label_ids": details.get("labelIds", []),
            })

        return {
            "count": len(emails),
            "emails": emails,
        }

    except HttpError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gmail API request failed: {exc}",
        ) from exc


# --------------------------------------------------
# Optional: run with `python -m app.main`
# Uvicorn CLI is recommended for development.
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=4000,
        reload=True,
    )
