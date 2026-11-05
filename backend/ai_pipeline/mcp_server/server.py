"""MCP server with role-based tool access control."""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from ai_pipeline.mcp_server.roles import VALID_ROLES, get_tools_for_role
from ai_pipeline.mcp_server.backend.fake import FakeBackend


class MCPServer:
    """Simple MCP server implementation without external MCP library."""

    def __init__(self, backend_type: str, role: str, access_token: Optional[str] = None):
        """
        Initialize MCP server.

        Args:
            backend_type: "fake" or "gmail"
            role: One of: sync, categorizer, drafter, inspector, sender
            access_token: Gmail access token (required for Gmail backend)
        """
        self.role = role
        self.backend_type = backend_type
        self.tools: Dict[str, Any] = {}

        if backend_type == "fake":
            self.backend = FakeBackend()
        else:
            raise ValueError(f"Unknown backend: {backend_type}")

        self._register_tools()

    def _register_tools(self):
        """Register tools allowed for this role."""
        allowed_tools = get_tools_for_role(self.role)

        if "list_threads" in allowed_tools:
            self.tools["list_threads"] = {
                "description": "List threads matching query.",
                "handler": self._list_threads,
            }

        if "get_thread" in allowed_tools:
            self.tools["get_thread"] = {
                "description": "Get full thread by ID.",
                "handler": self._get_thread,
            }

        if "create_draft" in allowed_tools:
            self.tools["create_draft"] = {
                "description": "Create a draft reply.",
                "handler": self._create_draft,
            }

        if "send_draft" in allowed_tools:
            self.tools["send_draft"] = {
                "description": "Send a draft.",
                "handler": self._send_draft,
            }

    async def _list_threads(
        self, query: str = "", max_results: int = 20, page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """List threads matching query."""
        try:
            results, next_token = await self.backend.list_threads(
                query, max_results, page_token
            )
            return {
                "threads": [r.model_dump() for r in results],
                "next_page_token": next_token,
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get full thread by ID."""
        try:
            thread = await self.backend.get_thread(thread_id)
            return {"thread": thread.model_dump()}
        except Exception as e:
            return {"error": str(e)}

    async def _create_draft(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None,
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a draft reply."""
        try:
            draft = await self.backend.create_draft(thread_id, body, subject, to, cc)
            return {"draft": draft.model_dump()}
        except Exception as e:
            return {"error": str(e)}

    async def _send_draft(
        self, draft_id: str, approval_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a draft."""
        try:
            message_id = await self.backend.send_draft(draft_id)
            return {"message_id": message_id}
        except Exception as e:
            return {"error": str(e)}

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "name": name,
                "description": tool["description"],
            }
            for name, tool in self.tools.items()
        ]

    def run(self):
        """Run the MCP server (simple stdio interface)."""
        print(f"MCP Server started with role: {self.role}, backend: {self.backend_type}")
        print(f"Available tools: {', '.join(self.tools.keys())}")
        print("Ready for connections (stdio transport)")

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request = json.loads(line)
                    response = self._handle_request(request)
                    print(json.dumps(response), flush=True)
                except json.JSONDecodeError:
                    print(json.dumps({"error": "Invalid JSON"}), flush=True)
        except KeyboardInterrupt:
            print("Server shutting down...", file=sys.stderr)
        except EOFError:
            print("Server connection closed", file=sys.stderr)

    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        method = request.get("method")

        if method == "tools/list":
            return {"tools": self.get_tools()}

        elif method == "tools/call":
            tool_name = request.get("params", {}).get("name")
            tool_args = request.get("params", {}).get("arguments", {})

            if tool_name not in self.tools:
                return {"error": f"Tool not found: {tool_name}"}

            # For now, return a placeholder since we can't await in this context
            return {"result": f"Tool {tool_name} called with args: {tool_args}"}

        else:
            return {"error": f"Unknown method: {method}"}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inbox Copilot MCP Server")
    parser.add_argument(
        "--role",
        required=True,
        choices=list(VALID_ROLES),
        help="Role for tool access",
    )
    parser.add_argument(
        "--backend",
        required=True,
        choices=["fake"],
        help="Backend to use",
    )

    args = parser.parse_args()

    try:
        server = MCPServer(args.backend, args.role)
        server.run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
