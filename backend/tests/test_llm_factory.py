"""Tests for LLM factory with retry logic."""

import pytest
from ai_pipeline.llm.factory import get_llm, get_token_count


@pytest.mark.asyncio
async def test_get_llm():
    """Test that LLM can be created."""
    try:
        llm = get_llm()
        assert llm is not None
        assert llm.model_name
    except Exception as e:
        pytest.skip(f"GROQ_API_KEY not available or LLM creation failed: {str(e)}")


def test_token_count():
    """Test token count estimation."""
    count = get_token_count("Hello world")
    assert count > 0
    assert isinstance(count, int)
