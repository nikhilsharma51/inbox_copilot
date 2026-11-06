"""Configuration for AI pipeline."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# Load environment variables from .env file
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)


class AIConfig:
    """AI pipeline configuration - reads from environment variables."""

    # Models for different tasks (from env or defaults)
    CLASSIFICATION_MODEL = os.getenv(
        "GROQ_MODEL_CLASSIFICATION", "llama-3.1-8b-instant"
    )
    CLASSIFICATION_FALLBACK = os.getenv(
        "GROQ_MODEL_FALLBACK", "openai/gpt-oss-20b"
    )

    DRAFTING_MODEL = os.getenv(
        "GROQ_MODEL_DRAFTING", "llama-3.3-70b-versatile"
    )
    DRAFTING_FALLBACK = os.getenv(
        "GROQ_MODEL_DRAFTING_FALLBACK", "openai/gpt-oss-120b"
    )

    EVAL_JUDGE_MODEL = os.getenv(
        "GROQ_MODEL_JUDGE", "llama-3.3-70b-versatile"
    )

    # Rate limits (from env or defaults)
    RATE_LIMIT_PER_MINUTE = int(
        os.getenv("AI_RATE_LIMIT_PER_MINUTE", "30")
    )
    RATE_LIMIT_TOKENS_PER_MINUTE = int(
        os.getenv("AI_RATE_LIMIT_TOKENS_PER_MINUTE", "10000")
    )

    # Token budgets (from env or defaults)
    TOKEN_BUDGET_CLASSIFICATION = int(
        os.getenv("AI_TOKEN_BUDGET_CLASSIFICATION", "600")
    )
    TOKEN_BUDGET_DRAFT = int(
        os.getenv("AI_TOKEN_BUDGET_DRAFT", "2500")
    )
    DAILY_TOKEN_BUDGET = int(
        os.getenv("AI_TOKEN_BUDGET_DAILY", "100000")
    )

    # Timeouts (from env or defaults)
    LLM_TIMEOUT_SECONDS = int(
        os.getenv("AI_LLM_TIMEOUT_SECONDS", "30")
    )
    MCP_CALL_TIMEOUT_SECONDS = int(
        os.getenv("AI_MCP_CALL_TIMEOUT_SECONDS", "20")
    )
    MCP_STARTUP_TIMEOUT_SECONDS = int(
        os.getenv("AI_MCP_STARTUP_TIMEOUT_SECONDS", "5")
    )

    # Versioning (from env or defaults)
    PROMPT_VERSION = os.getenv("AI_PROMPT_VERSION", "v1")
    MODEL_VERSION = os.getenv("AI_MODEL_VERSION", "phase-1")

    # Feature flags (from env or defaults)
    ENABLE_STRUCTURED_OUTPUT = os.getenv(
        "AI_ENABLE_STRUCTURED_OUTPUT", "true"
    ).lower() == "true"
    ENABLE_RETRY_ON_PARSE_ERROR = os.getenv(
        "AI_ENABLE_RETRY_ON_PARSE_ERROR", "true"
    ).lower() == "true"
    MAX_RETRIES_ON_429 = int(
        os.getenv("AI_MAX_RETRIES_ON_429", "2")
    )

    # Batch configuration (from env or defaults)
    BATCH_SIZE_CLASSIFICATION = int(
        os.getenv("AI_BATCH_SIZE_CLASSIFICATION", "5")
    )


def get_config() -> AIConfig:
    """Get AI configuration."""
    return AIConfig()
