from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal, User, Category, Thread
from app.routes.auth import _verify_session_cookie

router = APIRouter(prefix="/api", tags=["categories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/categories")
async def list_categories(request: Request, db: Session = Depends(get_db)):
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
    
    categories = db.query(Category).filter(Category.user_id == user_id).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "count": db.query(Thread).filter(
                Thread.user_id == user_id
            ).count()
        }
        for cat in categories
    ]
