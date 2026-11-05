"""Tests for role-based tool access control."""

import pytest
from ai_pipeline.mcp_server.roles import get_tools_for_role, role_can_use_tool, validate_role


def test_valid_roles():
    """Test that all defined roles are valid."""
    assert validate_role("sync")
    assert validate_role("categorizer")
    assert validate_role("drafter")
    assert validate_role("inspector")
    assert validate_role("sender")


def test_invalid_role():
    """Test that invalid role raises ValueError."""
    with pytest.raises(ValueError):
        get_tools_for_role("invalid")


def test_sync_tools():
    """Test that sync role has correct tools."""
    tools = get_tools_for_role("sync")
    assert "list_threads" in tools
    assert "send_draft" not in tools


def test_sender_tools():
    """Test that sender role only has send_draft."""
    tools = get_tools_for_role("sender")
    assert tools == {"send_draft"}


def test_role_can_use_tool():
    """Test role-tool permission checks."""
    assert role_can_use_tool("inspector", "list_threads")
    assert role_can_use_tool("inspector", "get_thread")
    assert not role_can_use_tool("inspector", "send_draft")
