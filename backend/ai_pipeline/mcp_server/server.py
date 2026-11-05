import argparse
import os
import sys
from typing import List, Optional

from fastmcp import FastMCP

from ai_pipeline.mcp_server.roles import VALID_ROLES, get_tools_for_role
from ai_pipeline.mcp_server.backend.fake import FakeBackend


class MCPServer :
    """MCP server with role-based tool registration."""
    def __init__(self, backend_type : str , role : str, access_token : Optional[str] = None) :
        """
        Initialize MCP server.

        Args:
        role: One of: sync, categorizer, drafter, inspector, sender
        backend_type: "fake" or "gmail"
        access_token: Gmail access token (required for Gmail backend)
        """

        self.role = role 
        self.backend_type = backend_type
        self.app = FastMCP("inbox-copilot-mcp")

        if backend_type == "fake":
            self.backend = FakeBackend()
        else:
            raise ValueError(f"Unknown backend : {backend_type}")

        self._register_tools()

    def _register_tools(self):
        """Register tools allowed for this role."""

        allowed_tools = get_tools_for_role(self.role)

        if "list_threads" in allowed_tools : 
            @self.app.tool()
            async def list_threads(
                query : str = "",
                max_results : int = 20,
                page_token: Optional[str] = None
            )-> dict :

                """
                List threads matching query.

                Args:
                query: Search query (case-insensitive)
                max_results: Max threads to return (1-25)
                page_token: Pagination token

                Returns:
                {threads: [...], next_page_token: "..."}
                """

                try:
                    results , next_token = await self.backend.list_threads(
                        query , max_results , page_token
                    )
                    return {
                        "threads": [r.model_dump() for r in results],
                        "next_page_token": next_token,
                    }
                except Exception as e :
                    return {"error": str(e)}

        if "get_thread" in allowed_tools :
            @self.app.tool()
            async def get_thread(thread_id : str) -> dict:
                """
                Get full thread by ID.

                Args:
                thread_id: ID of thread to fetch

                Returns:
                Thread object with all messages
                """

                try : 
                    thread = await self.backend.get_thread(thread_id)
                    return {"thread" : thread.model_dump()}
                except Exception as e : 
                    return {"error": str(e)}
        
        if "create_draft" in allowed_tools:
            @self.app.tool()
            async def create_draft(
                thread_id: str,
                body: str,
                subject: Optional[str] = None,
                to: Optional[List[str]] = None,
                cc: Optional[List[str]] = None,
            ) -> dict:
                """
                Create a draft reply.

                Args:
                    thread_id: ID of thread to reply in
                    body: Draft body text
                    subject: Subject (auto-generated if not provided)
                    to: Recipients (auto-detected from thread if not provided)
                    cc: CC recipients

                Returns:
                    Created draft object
                """
                try:
                    draft = await self.backend.create_draft(
                        thread_id, body, subject, to, cc
                    )
                    return {"draft": draft.model_dump()}
                except Exception as e:
                    return {"error": str(e)}

        if "send_draft" in allowed_tools:
            @self.app.tool()
            async def send_draft(
                draft_id: str,
                approval_token: Optional[str] = None
            ) -> dict:
                """
                Send a draft.

                Args:
                    draft_id: ID of draft to send
                    approval_token: Approval token from backend (for verification)

                Returns:
                    Message ID
                """
                try:
                    message_id = await self.backend.send_draft(draft_id)
                    return {"message_id": message_id}
                except Exception as e:
                    return {"error": str(e)}
    async def run(self):
        """Run the server."""
        await self.app.run(transport="stdio")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inbox Copilot MCP Server")
    parser.add_argument(
        "--role",
        required=True,
        choices=list(VALID_ROLES),
        help="Role for tool access"
    )
    parser.add_argument(
        "--backend",
        required=True,
        choices=["fake"],
        help="Backend to use"
    )

    args = parser.parse_args()

    try:
        server = MCPServer(args.backend, args.role)
        import asyncio
        asyncio.run(server.run())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()