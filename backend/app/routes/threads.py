import json
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal, User, Thread, Draft
from app.routes.auth import _verify_session_cookie
from app.gmail import get_mailbox, ReconnectNeeded
from ai_pipeline.preprocess import clean_email

router = APIRouter(prefix="/api", tags=["threads"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str, 
    request: Request, 
    db: Session = Depends(get_db)
):

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
    
    thread = db.query(Thread).filter(
        Thread.id == thread_id,         
        Thread.user_id == user_id    
    ).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    try:
        mailbox = get_mailbox(user)
        gmail_thread = mailbox.get_thread(thread.gmail_thread_id)
        
        if not gmail_thread:
            raise HTTPException(status_code=404, detail="Thread not found in mailbox")
    
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="Please reconnect your Gmail account")
    except Exception as e:
        raise HTTPException(status_code=502, detail="Failed to fetch thread from Gmail")
    
    drafts = db.query(Draft).filter(
        Draft.thread_id == thread_id,
        Draft.user_id == user_id
    ).all()
    
    return {
        "id": thread.id,
        "thread_id": thread.gmail_thread_id,
        "subject": thread.subject,
        "sender": thread.sender,
        "summary": thread.summary,
        "status": thread.status,
        "needs_reply": thread.needs_reply,
        "priority": thread.priority,
        "confidence": thread.confidence,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        
        "messages": [
            {
                "sender": msg.sender,
                "to": msg.to,
                "date": msg.date.isoformat() if msg.date else None,
                "body": clean_email(msg.body),
                "is_from_me": msg.sender == user.email
            }
            for msg in gmail_thread.messages
        ],
        
        "drafts": [
            {
                "id": d.id,
                "subject": d.subject,
                "body": d.body,
                "to_addr": d.to_addr,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
                "warnings": json.loads(d.warnings) if d.warnings else []
            }
            for d in drafts
        ]
    }
