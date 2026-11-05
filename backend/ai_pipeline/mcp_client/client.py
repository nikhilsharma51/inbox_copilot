import os
import sys
import logging
import subprocess
import time
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MCPClientManager:

    def __init__(self, timeout_startup: int = 5, timeout_call: int = 20):
        self.timeout_startup = timeout_startup
        self.timeout_call = timeout_call
        self.process: Optional[subprocess.Popen] = None

    async def start_server(
        self,
        role: str,
        backend: str,
        access_token: Optional[str] = None
    ) -> None:

        cmd = [
            sys.executable,
            "-m",
            "ai_pipeline.mcp_server",
            "--role", role,
            "--backend", backend,
        ]

        env = os.environ.copy()

        if access_token:
            env["ACCESS_TOKEN"] = access_token

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

            logger.info(f"Started MCP server (PID {self.process.pid})")

        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}") from e

        start_time = time.time()

        while True:

            if self.process.poll() is not None:
                raise RuntimeError("MCP server crashed")

            elapsed = time.time() - start_time

            if elapsed > self.timeout_startup:
                self.process.terminate()
                raise TimeoutError("MCP server startup timed out")

            # Process is alive, but MCP readiness is not verified.
            if elapsed >= 0.5:
                logger.info("MCP server process is running")
                return

            await asyncio.sleep(0.1)

    async def stop_server(self) -> None:

        if self.process:

            try:
                self.process.terminate()
                await asyncio.to_thread(self.process.wait, timeout=5)

            except subprocess.TimeoutExpired:
                self.process.kill()
                await asyncio.to_thread(self.process.wait)

            finally:
                self.process = None
                logger.info("MCP server stopped!")


async def get_tools(
    role: str,
    backend: str,
    access_token: Optional[str] = None
) -> List[Dict[str, Any]]:

    manager = MCPClientManager()

    try:
        await manager.start_server(role, backend, access_token)

        return []

    finally:
        await manager.stop_server()