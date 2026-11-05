import argparse
import os
import sys
from typing import List, Optional

from fastmcp import FastMCP

from ai_pipeline.mcp_server.roles import VALID_ROLES, get_tools_for_role
from ai_pipeline.mcp_server.backend.fake import FakeBackend


class MCPServer :
    def __init__(self, backend_type : str , role : str, access_token : Optional[str] = None) :
        self.role = role 
        self.backend_type = backend_type
        self.app = FastMCP("inbox-copilot-mcp")

        if backend_type == "fake":
            self.backend = FakeBackend()
        else:
            raise ValueError(f"Unknown backend : {backend_type}")

        self._register_tools()

    def _register_tools(self):

        allowed_tools = get_tools_for_role(self.role)

        if "list_threads" in allowed_tools : 
            @self.app.tool()
            async def list_threads(
                query : str = "",
                max_results : int = 20,
                page_token: Optional[str] = None
            )-> dict :
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
                try:
                    message_id = await self.backend.send_draft(draft_id)
                    return {"message_id": message_id}
                except Exception as e:
                    return {"error": str(e)}
    async def run(self):
        await self.app.run(transport="stdio")

def main():
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