from pydantic import BaseModel, Field


class Classification(BaseModel):
    category: str
    summary: str = Field(max_length=160)
    needs_reply: bool
    priority: int
    confidence: float
    suspected_injection: bool = False
