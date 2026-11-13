from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentState, create_agent
from pydantic import BaseModel
from langchain.tools import tool
from datetime import datetime

from ai_pipeline.config import DRAFT_MODEL

load_dotenv()

MODEL = "qwen/qwen3-32b"

class MyState(AgentState):
    current_time: datetime


@tool
def get_time() -> str:
    """Return the current time."""
    now = datetime.now()
    return now.isoformat()


tools = [get_time]

llm = ChatGroq(
    model=DRAFT_MODEL,
    temperature=0
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="Return the current time.",
    state_schema=MyState
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is the current time?"}
    ]
})

print(result)
