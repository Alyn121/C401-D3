from __future__ import annotations

import random
import time
from dataclasses import dataclass
from .tracing import observe

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    @observe(as_type="generation")
    def generate(self, prompt: str) -> FakeResponse:
        # Chaos Mode: Random Latency (0.1s to 2.5s)
        delay = random.uniform(0.1, 2.5)
        # Occasionally spike to 5s to trigger P95 alerts
        if random.random() < 0.1:
            delay = random.uniform(4.0, 6.0)
        time.sleep(delay)

        # Chaos Mode: Random Timeout (5% chance)
        if random.random() < 0.05:
            raise TimeoutError("LLM Request Timed Out (Chaos Mode)")

        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = (
            "Starter answer. Teams should improve this output logic and add better quality checks. "
            "Use retrieved context and keep responses concise."
        )
        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)
