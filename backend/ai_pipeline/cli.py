import asyncio 
import argparse
import sys
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.tools import Tool
from langchain.agents import create_agent

from ai_pipeline.llm.factory import get_llm
from ai_pipeline.mcp_client.client import get_tools
from ai_pipeline.config import get_config

config = get_config()

def format_tools_for_agent(mcp_tools : list) -> list[Tool] :
    tools = []
    
    for tool_def in mcp_tools :
        tool =Tool(
            name= tool_def["name"],
            func=lambda x, n=tool_def["name"]: f"[Called {n}]",
            description=tool_def["description"],
            
        )
        tools.append(tool)
    
    return tools

async def run_agent(
    backend: str = "fake",
    max_iterations: int = 6,
) -> None:
    print("📧 Inbox Copilot Agent")
    print(f"Backend: {backend} | Max steps: {max_iterations}\n")

    try:
        mcp_tools = await get_tools("inspector", backend)

        tools = format_tools_for_agent(mcp_tools)

        llm = get_llm()

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an email assistant. Use tools to look things up."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are an email assistant. "
                "Use the available tools to look up emails "
                "and answer user questions accurately."
            ),
        )

        while True:
            user_input = input("\nYou: ").strip()

            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            if not user_input:
                continue

            try:
                result = await agent.ainvoke(
                    {
                        "messages": [
                            {"role": "user", "content": user_input}
                        ]
                    },
                    config={
                        "recursion_limit": (max_iterations * 2) + 1
                    },
                )

                response = result["messages"][-1].content
                print(f"Agent: {response}")

            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"Fatal error: {e}")
        
        
def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inbox Copilot Terminal Agent")
    parser.add_argument(
        "--backend",
        choices=["fake"],
        default="fake",
        help="Backend to use"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="Max agent steps before terminating"
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_agent(args.backend, args.max_steps))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()