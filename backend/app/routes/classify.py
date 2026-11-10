from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal, User, Thread
from app.routes.auth import _verify_session_cookie
from app.gmail import get_mailbox, ReconnectNeeded
from ai_pipeline.pipeline import classify_new_threads

router = APIRouter(prefix="/api", tags=["classify"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/classify")
async def classify(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="Please reconnect your Gmail account")
    
    def run_classification():
        new_db = SessionLocal()
        try:
            classify_new_threads(new_db, user, mailbox, limit=25)
        finally:
            new_db.close()
    
    background_tasks.add_task(run_classification)
    
    return {"started": True}


@router.get("/status")
async def status(request: Request, db: Session = Depends(get_db)):
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
    
    total = db.query(Thread).filter(Thread.user_id == user_id).count()
    classified = db.query(Thread).filter(
        Thread.user_id == user_id,
        Thread.status != 'new'
    ).count()
    
    return {"classified": classified, "total": total}
