from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class LLMResponse:
    def __init__(
        self,
        content: str,
        provider: str,
        model: str,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ):
        self.content = content
        self.provider = provider
        self.model = model
        self.latency_ms = latency_ms
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.estimated_cost_usd = estimated_cost_usd


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def complete(self, system: str, user: str, temperature: float = 0.3) -> LLMResponse:
        """Return a plain-text completion."""

    @abstractmethod
    def complete_structured(
        self,
        system: str,
        user: str,
        schema: Type[BaseModel],
        temperature: float = 0.1,
    ) -> tuple[BaseModel, LLMResponse]:
        """Return a Pydantic model instance parsed from structured output."""
