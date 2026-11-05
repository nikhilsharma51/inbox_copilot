"""Tests for MCP client manager."""

import pytest
from ai_pipeline.mcp_client.client import MCPClientManager


@pytest.mark.asyncio
async def test_client_manager_init():
    """Test MCPClientManager initialization."""
    manager = MCPClientManager()
    assert manager.process is None
    assert manager.timeout_startup == 5
