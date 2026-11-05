"""Tests for hash utilities for draft approval verification."""

from ai_pipeline.mcp_server.hash_utility import compute_hash, verify_hash, norm_text, norm_addrs


def test_norm_text_line_endings():
    """Test that different line endings produce same hash."""
    h1 = compute_hash("a@b.com", "", "Test", "Line1\nLine2", "t1")
    h2 = compute_hash("a@b.com", "", "Test", "Line1\r\nLine2", "t1")
    assert h1 == h2


def test_norm_addrs_order():
    """Test that address order doesn't affect hash."""
    h1 = compute_hash("a@b.com, c@d.com", "", "Test", "Body", "t1")
    h2 = compute_hash("c@d.com, a@b.com", "", "Test", "Body", "t1")
    assert h1 == h2


def test_tampered_body():
    """Test that body modification changes hash."""
    h1 = compute_hash("a@b.com", "", "Test", "Body", "t1")
    h2 = compute_hash("a@b.com", "", "Test", "Body modified", "t1")
    assert h1 != h2


def test_verify_hash():
    """Test hash verification."""
    h = compute_hash("a@b.com", "", "Test", "Body", "t1")
    assert verify_hash("a@b.com", "", "Test", "Body", "t1", h)
    assert not verify_hash("a@b.com", "", "Test", "Body modified", "t1", h)
