"""Terminal agent CLI for chatbot interaction."""

import asyncio
import argparse
import sys
from typing import Optional

from ai_pipeline.llm.factory import get_llm
from ai_pipeline.mcp_client.client import get_tools
from ai_pipeline.config import get_config

config = get_config()


def format_tools_for_display(mcp_tools: list) -> str:
    """Format tools for display."""
    if not mcp_tools:
        return "No tools available"
    
    lines = []
    for i, tool in enumerate(mcp_tools, 1):
        lines.append(f"  {i}. {tool.get('name', 'unknown')}")
    return "\n".join(lines)


async def run_agent(
    backend: str = "fake",
    max_iterations: int = 6,
) -> None:
    """
    Run terminal agent loop.
    
    Args:
        backend: "fake"
        max_iterations: Max steps before terminating
    """
    print("=" * 60)
    print("Inbox Copilot Agent")
    print("=" * 60)
    print(f"Backend: {backend} | Max steps: {max_iterations}")
    print("Type 'help' for commands, 'quit' to exit\n")

    try:
        # Get MCP tools
        mcp_tools = await get_tools("inspector", backend)
        
        if mcp_tools:
            print("Available tools:")
            print(format_tools_for_display(mcp_tools))
            print()
        
        # Get LLM (optional, will warn if not available)
        try:
            llm = get_llm()
            print(f"LLM Model: {llm.model_name}\n")
        except Exception as e:
            print(f"Warning: LLM not available - {str(e)}\n")
            llm = None

        # Simple chat loop
        step_count = 0
        while step_count < max_iterations:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            if user_input.lower() == "help":
                print("\nCommands:")
                print("  help     - Show this help message")
                print("  tools    - List available tools")
                print("  quit     - Exit the agent")
                print("  Any other input will be sent to the LLM\n")
                continue

            if user_input.lower() == "tools":
                print("\nAvailable tools:")
                print(format_tools_for_display(mcp_tools))
                print()
                continue

            step_count += 1
            print(f"\n[Step {step_count}/{max_iterations}]")

            try:
                # For now, just echo back a simple response
                # In a full implementation, this would call the LLM with tools
                response = f"You asked: '{user_input}'\n(Tool calling not yet implemented in this CLI)"
                print(f"Agent: {response}\n")
            except Exception as e:
                print(f"Error: {e}\n")
                step_count -= 1

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inbox Copilot Terminal Agent")
    parser.add_argument(
        "--backend",
        choices=["fake"],
        default="fake",
        help="Backend to use (default: fake)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=6,
        help="Max agent steps before terminating (default: 6)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_agent(args.backend, args.max_steps))
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
