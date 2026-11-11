import json
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal, User, Thread, Draft
from app.routes.auth import _verify_session_cookie
from app.gmail import get_mailbox, ReconnectNeeded
from ai_pipeline.draft import write_draft, flag_draft, pick_recipients, recipient_warning, DraftFailed
from ai_pipeline.preprocess import clean_email

router = APIRouter(prefix="/api", tags=["drafts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/threads/{thread_id}/drafts")
async def create_draft(thread_id: str, payload: dict, request: Request, db: Session = Depends(get_db)):
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
    
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    try:
        mailbox = get_mailbox(user)
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="Please reconnect your Gmail account")
    
    try:
        gmail_thread = mailbox.get_thread(thread.gmail_thread_id)
    except:
        raise HTTPException(status_code=404, detail="Thread not found in mailbox")
    
    if not gmail_thread:
        raise HTTPException(status_code=404, detail="Thread not found in mailbox")
    
    instruction = payload.get("instruction", "")
    style = payload.get("style", "professional")
    
    try:
        draft_out = write_draft(gmail_thread, instruction, style, user.email, llm=None)
    except DraftFailed as e:
        raise HTTPException(status_code=502, detail="Failed to generate draft. Please try again.")
    
    warnings = flag_draft(draft_out, gmail_thread, instruction)
    recip_warning = recipient_warning(gmail_thread)
    
    to_addr = ", ".join(pick_recipients(gmail_thread, user.email))
    
    draft = Draft(
        user_id=user_id,
        thread_id=thread_id,
        to_addr=to_addr,
        subject=draft_out.subject,
        body=draft_out.body,
        instruction=instruction,
        warnings=json.dumps(warnings),
        status="draft"
    )
    
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    return {
        "id": draft.id,
        "subject": draft.subject,
        "body": draft.body,
        "to_addr": draft.to_addr,
        "status": draft.status,
        "warnings": warnings,
        "recipient_warning": recip_warning,
        "needs_info": draft_out.needs_info
    }


@router.patch("/drafts/{draft_id}")
async def edit_draft(draft_id: str, payload: dict, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        user_id = _verify_session_cookie(session_token)
    except HTTPException:
        raise
    
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft.status != "draft":
        raise HTTPException(status_code=409, detail="Cannot edit draft with status " + draft.status)
    
    if "subject" in payload:
        draft.subject = payload["subject"]
    if "body" in payload:
        draft.body = payload["body"]
    
    thread = db.query(Thread).filter(Thread.id == draft.thread_id).first()
    if thread:
        try:
            mailbox_user = db.query(User).filter(User.id == user_id).first()
            mailbox = get_mailbox(mailbox_user)
            gmail_thread = mailbox.get_thread(thread.gmail_thread_id)
            
            warnings = flag_draft(
                type('', (), {'subject': draft.subject, 'body': draft.body, 'needs_info': []})(),
                gmail_thread,
                draft.instruction or ""
            )
            draft.warnings = json.dumps(warnings)
        except:
            pass
    
    db.commit()
    db.refresh(draft)
    
    return {
        "id": draft.id,
        "subject": draft.subject,
        "body": draft.body,
        "status": draft.status,
        "warnings": json.loads(draft.warnings) if draft.warnings else []
    }


@router.post("/drafts/{draft_id}/discard")
async def discard_draft(draft_id: str, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        user_id = _verify_session_cookie(session_token)
    except HTTPException:
        raise
    
    draft = db.query(Draft).filter(Draft.id == draft_id, Draft.user_id == user_id).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft.status != "draft":
        raise HTTPException(status_code=409, detail="Cannot discard draft with status " + draft.status)
    
    draft.status = "discarded"
    db.commit()
    
    return {"status": "discarded"}


@router.get("/threads/{thread_id}/drafts")
async def list_drafts(thread_id: str, request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        user_id = _verify_session_cookie(session_token)
    except HTTPException:
        raise
    
    thread = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    drafts = db.query(Draft).filter(
        Draft.thread_id == thread_id,
        Draft.user_id == user_id
    ).order_by(Draft.created_at.desc()).all()
    
    return [
        {
            "id": d.id,
            "subject": d.subject,
            "body": d.body,
            "to_addr": d.to_addr,
            "status": d.status,
            "warnings": json.loads(d.warnings) if d.warnings else [],
            "created_at": d.created_at
        }
        for d in drafts
    ]
