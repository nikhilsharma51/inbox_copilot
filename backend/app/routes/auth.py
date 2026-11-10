import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Cookie
from sqlalchemy.orm import Session

from app.auth import encrypt_token, decrypt_token, TokenDecryptError
from app.config import settings
from app.db import SessionLocal, User

router = APIRouter(prefix="/api/auth", tags=["auth"])

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


def _make_session_cookie(user_id: str) -> str:
    from itsdangerous import TimestampSigner
    signer = TimestampSigner(settings.session_secret)
    signed = signer.sign(user_id)
    return signed.decode() if isinstance(signed, bytes) else signed


def _verify_session_cookie(token: str) -> str:
    from itsdangerous import TimestampSigner, SignatureExpired, BadSignature
    signer = TimestampSigner(settings.session_secret)
    try:
        user_id = signer.unsign(token, max_age=86400 * 30)
        return user_id if isinstance(user_id, str) else user_id.decode()
    except (SignatureExpired, BadSignature) as e:
        raise HTTPException(status_code=401, detail="Invalid or expired session") from e


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/login")
async def login():
    state = secrets.token_urlsafe(32)
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    response = Response(status_code=302)
    response.headers["Location"] = auth_url
    response.set_cookie(
        "oauth_state",
        state,
        max_age=600,
        httponly=True,
        samesite="Lax",
        secure=settings.frontend_origin.startswith("https"),
    )
    
    return response


@router.get("/callback")
async def callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    state_cookie = request.cookies.get("oauth_state")
    
    if not state_cookie or state != state_cookie:
        raise HTTPException(status_code=400, detail="Invalid or missing state")
    
    token_response = await _exchange_code_for_tokens(code)
    
    if "error" in token_response:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_response.get('error')}")
    
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")
    
    user_info = await _get_user_info(access_token)
    
    if "error" in user_info:
        raise HTTPException(status_code=400, detail=f"Failed to get user info: {user_info.get('error')}")
    
    granted_scopes = token_response.get("scope", "").split()
    required_scopes = set(GMAIL_SCOPES)
    granted_scopes_set = set(granted_scopes)
    
    if not required_scopes.issubset(granted_scopes_set):
        raise HTTPException(
            status_code=403,
            detail=f"Missing required Gmail scopes. Got: {granted_scopes_set}, Required: {required_scopes}"
        )
    
    google_sub = user_info.get("sub")
    email = user_info.get("email")
    
    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Missing sub or email from Google")
    
    user = db.query(User).filter(User.google_sub == google_sub).first()
    
    if not user:
        user = User(google_sub=google_sub, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    if refresh_token:
        user.refresh_token_enc = encrypt_token(refresh_token)
        db.commit()
    
    session_token = _make_session_cookie(user.id)
    
    response = Response(status_code=302)
    response.headers["Location"] = settings.frontend_origin
    response.set_cookie(
        "session",
        session_token,
        max_age=86400 * 30,
        httponly=True,
        samesite="Lax",
        secure=settings.frontend_origin.startswith("https"),
    )
    response.delete_cookie("oauth_state")
    
    return response


@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        user_id = _verify_session_cookie(session_token)
    except HTTPException:
        raise
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "google_sub": user.google_sub,
    }


@router.post("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    response = Response(status_code=200, content="Logged out")
    response.delete_cookie("session")
    
    return response


@router.post("/disconnect")
async def disconnect(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        user_id = _verify_session_cookie(session_token)
    except HTTPException:
        raise
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.refresh_token_enc:
        raise HTTPException(status_code=400, detail="No refresh token to revoke")
    
    try:
        refresh_token = decrypt_token(user.refresh_token_enc)
    except TokenDecryptError:
        raise HTTPException(status_code=400, detail="Failed to decrypt refresh token")
    
    revoke_failed = False
    try:
        await _revoke_token(refresh_token)
    except Exception:
        revoke_failed = True
    
    user.refresh_token_enc = None
    db.commit()
    
    if revoke_failed:
        return {"message": "Revoked locally but remote revoke failed", "warning": True}
    
    return {"message": "Disconnected successfully"}


async def _exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        return response.json()


async def _get_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


async def _revoke_token(refresh_token: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_REVOKE_URL,
            data={"token": refresh_token},
        )
        if response.status_code != 200:
            raise Exception(f"Revoke failed with status {response.status_code}")
