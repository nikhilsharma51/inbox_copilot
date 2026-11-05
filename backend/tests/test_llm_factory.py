"""Tests for LLM factory with retry logic."""

import os
import pytest
from ai_pipeline.llm.factory import get_llm, get_token_count


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set"
)
async def test_get_llm():
    """Test that LLM can be created."""
    llm = get_llm()
    assert llm is not None
    assert llm.model_name


def test_token_count():
    """Test token count estimation."""
    count = get_token_count("Hello world")
    assert count > 0
    assert isinstance(count, int)
