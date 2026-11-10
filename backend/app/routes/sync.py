from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal, User, Thread
from app.routes.auth import _verify_session_cookie, get_db
from app.gmail import get_mailbox, ReconnectNeeded
from app.sync import sync_threads

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync")
async def sync(request: Request, db: Session = Depends(get_db)):
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
    
    try:
        mailbox = get_mailbox(user)
        result = sync_threads(db, user, mailbox)
        return result
    
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="Please reconnect your Gmail account")


@router.get("/threads")
async def list_threads(request: Request, db: Session = Depends(get_db)):
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
    
    threads = db.query(Thread).filter(
        Thread.user_id == user_id
    ).order_by(Thread.created_at.desc()).limit(200).all()
    
    return [
        {
            "id": t.id,
            "thread_id": t.gmail_thread_id,
            "subject": t.subject,
            "sender": t.sender,
            "summary": t.summary,
            "status": t.status,
            "created_at": t.created_at,
        }
        for t in threads
    ]
