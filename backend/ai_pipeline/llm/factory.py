
import asyncio
import logging
import time
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from langchain_groq import ChatGroq

from ai_pipeline.config import get_config

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def get_llm(model_name: Optional[str] = None) -> ChatGroq:
    config = get_config()
    model = model_name or config.CLASSIFICATION_MODEL

    return ChatGroq(
        model=model,
        temperature=0,
        max_retries=0,
        timeout=config.LLM_TIMEOUT_SECONDS,
    )


def get_llm_with_structured_output(
    model_name: Optional[str],
    schema: Type[T]
):
    llm = get_llm(model_name)

    if get_config().ENABLE_STRUCTURED_OUTPUT:
        llm = llm.with_structured_output(
            schema,
            method="json_mode"
        )

    return llm


async def call_llm_with_retry(
    llm,
    messages: list,
    max_retries: Optional[int] = None
) -> Optional[str]:
    config = get_config()

    if max_retries is None:
        max_retries = config.MAX_RETRIES_ON_429

    for attempt in range(max_retries + 1):
        try:
            response = await llm.ainvoke(messages)
            return response.content

        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                if attempt < max_retries:
                    wait_time = 2 ** attempt

                    logger.warning(
                        f"Rate limited. Waiting {wait_time}s "
                        f"before retry {attempt + 1}/{max_retries}"
                    )

                    await asyncio.sleep(wait_time)
                    continue

                raise Exception(
                    f"Rate limited after {max_retries} retries"
                ) from e

            raise


def get_token_count(text: str) -> int:
    return len(text) // 4
