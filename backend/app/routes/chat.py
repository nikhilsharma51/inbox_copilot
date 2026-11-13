from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.auth import get_session_user
from app.db import get_db
from app.gmail import get_mailbox, ReconnectNeeded
from ai_pipeline.agent import run_agent
from ai_pipeline.llm import call_with_retry

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[str]


@router.post("/api/chat")
def chat(req: ChatRequest, user=Depends(get_session_user), db=Depends(get_db)):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=422, detail="message is required")
    
    if len(req.message) > 2000:
        raise HTTPException(status_code=422, detail="message must be 2000 characters or less")
    
    try:
        mail = get_mailbox(user, db)
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="mailbox needs reconnecting")
    
    try:
        answer, tool_calls = call_with_retry(
            lambda: run_agent(db, user, mail, req.message)
        )
        return ChatResponse(answer=answer, tool_calls=tool_calls)
    except ReconnectNeeded:
        raise HTTPException(status_code=401, detail="mailbox needs reconnecting")
    except Exception as e:
        if "429" in str(e) or "rate limit" in str(e).lower():
            raise HTTPException(status_code=503, detail="service temporarily unavailable, try again later")
        raise
