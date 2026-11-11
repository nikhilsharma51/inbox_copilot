from pydantic import BaseModel, Field


class Classification(BaseModel):
    category: str
    summary: str = Field(max_length=160)
    needs_reply: bool
    priority: int
    confidence: float
    suspected_injection: bool = False


class DraftOut(BaseModel):
    subject: str
    body: str
    needs_info: list[str] = Field(default_factory=list)
