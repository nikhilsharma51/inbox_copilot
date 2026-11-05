import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


@dataclass
class Step:
    type: str  # "llm", "tool", "guard", etc.
    name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "name": self.name,
            "input": str(self.input_data)[:100],
            "output": str(self.output_data)[:100] if self.output_data else None,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }


class TracingCallback(BaseCallbackHandler):
    def __init__(self):
        self.steps: List[Step] = []
        self.current_step: Optional[Step] = None
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.start_time = time.time()

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
          **kwargs: Any,
    ) -> None:
        self.current_step = Step(
            type="llm",
            name=serialized.get("name", "unknown"),
            input_data={"prompts_count": len(prompts)},
        )

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        if self.current_step:
            # Extract tokens
            if hasattr(response, 'llm_output') and isinstance(response.llm_output, dict):
                usage = response.llm_output.get('usage', {})
                self.current_step.tokens_in = usage.get('prompt_tokens', 0)
                self.current_step.tokens_out = usage.get('completion_tokens', 0)

            self.current_step.output_data = {"generations_count": len(response.generations)}
            self.current_step.latency_ms = (time.time() - self.current_step.timestamp) * 1000
            self.steps.append(self.current_step)

            self.total_tokens_in += self.current_step.tokens_in
            self.total_tokens_out += self.current_step.tokens_out

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
          **kwargs: Any,
    ) -> None:
        self.current_step = Step(
            type="tool",
            name=serialized.get("name", "unknown"),
            input_data={"input": input_str[:200]},
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if self.current_step:
            self.current_step.output_data = {"output": output[:200]}
            self.current_step.latency_ms = (time.time() - self.current_step.timestamp) * 1000
            self.steps.append(self.current_step)

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        if self.current_step:
            self.current_step.error = str(error)
            self.steps.append(self.current_step)

    def print_summary(self) -> None:
        total_latency_ms = (time.time() - self.start_time) * 1000

        print("\nExecution Trace:")
        print("-" * 80)
        for i, step in enumerate(self.steps, 1):
            print(f"{i:2}. {step.type:8} {step.name:20} latency={step.latency_ms:6.1f}ms")

        print("-" * 80)
        print(f"Total steps: {len(self.steps)}")
        print(f"Total tokens in: {self.total_tokens_in}")
        print(f"Total tokens out: {self.total_tokens_out}")
        print(f"Total latency: {total_latency_ms:.1f}ms")