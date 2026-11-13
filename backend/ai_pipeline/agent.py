import sys
from typing import Any
from pathlib import Path

from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

from ai_pipeline.llm import get_llm, call_with_retry
from ai_pipeline.config import DRAFT_MODEL
from ai_pipeline.tools import make_tools


def build_agent(db: Any, user: Any, mail: Any, llm: Any = None) -> tuple[Any, list]:
    prompt_path = Path(__file__).parent.parent / "prompts" / "agent_v1.md"
    system_prompt = prompt_path.read_text().strip()
    
    model = llm or get_llm(DRAFT_MODEL)
    tools = make_tools(db, user, mail)
    
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt
    )
    
    return agent, tools


def _trace_tool_call(tool_name: str, args: dict) -> None:
    arg_strs = []
    for k, v in args.items():
        v_str = str(v)
        if len(v_str) > 80:
            v_str = v_str[:80]
        arg_strs.append(f"{k}={v_str}")
    args_repr = ", ".join(arg_strs)
    print(f"tool: {tool_name}({args_repr})", file=sys.stderr)


def run_agent(db: Any, user: Any, mail: Any, message: str, llm: Any = None) -> tuple[str, list[str]]:
    agent, tools = build_agent(db, user, mail, llm)
    tool_calls_made = []
    answer_text = ""
    
    try:
        config = {"recursion_limit": 10}
        result = call_with_retry(lambda: agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config
        ))
        
        if hasattr(result, "get"):
            messages = result.get("messages", [])
        else:
            messages = getattr(result, "messages", [])
        
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    if tool_name:
                        tool_calls_made.append(tool_name)
                        args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                        _trace_tool_call(tool_name, args or {})
            
            if hasattr(msg, "type") and msg.type == "ai":
                if hasattr(msg, "content"):
                    answer_text = msg.content
        
        return (answer_text, tool_calls_made)
    
    except GraphRecursionError:
        return ("I could not finish that within the step limit. Try a more specific question.", tool_calls_made)
