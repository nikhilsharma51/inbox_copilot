import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from app.config import settings

load_dotenv()

class EmailClassification(BaseModel):
    category: str
    summary: str = Field(max_length=160)
    needs_reply: bool
    priority: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)

with open("data/fixtures.json", "r", encoding="utf-8") as f:
    fixtures = json.load(f)

thread = fixtures["threads"][0]
message = thread["messages"][0]

email_text = f"""
Subject: {thread["subject"]}
Sender: {message["sender"]}
Body: {message["body"]}
"""

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=settings.groq_api_key
)

structured_model = model.with_structured_output(EmailClassification)

result = structured_model.invoke(
    f"""
    Classify this email.

    Available categories: Internship, Placement, Newsletter, Hackathon, Other

    Priority: 1=Urgent, 2=Important, 3=Normal, 4=Low, 5=Ignore

    Email:
    {email_text}
    """
)

print("Result:", result)
print("Type:", type(result))
print("Category:", result.category)
print("Confidence:", result.confidence)
print("Needs Reply:", result.needs_reply)
