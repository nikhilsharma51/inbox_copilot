"""Tests for AI pipeline configuration."""

from ai_pipeline.config import get_config


def test_config_models_exist():
    """Test that required model names are configured."""
    config = get_config()
    assert config.CLASSIFICATION_MODEL
    assert config.DRAFTING_MODEL


def test_rate_limits_reasonable():
    """Test that rate limits are set to positive values."""
    config = get_config()
    assert config.RATE_LIMIT_PER_MINUTE > 0
    assert config.DAILY_TOKEN_BUDGET > 0


def test_timeouts_set():
    """Test that timeouts are configured."""
    config = get_config()
    assert config.LLM_TIMEOUT_SECONDS > 0
    assert config.MCP_STARTUP_TIMEOUT_SECONDS > 0
