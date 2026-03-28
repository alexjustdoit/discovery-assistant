from __future__ import annotations

import json
import os
import time
from typing import Type

import httpx
from pydantic import BaseModel

from llm.providers.base import LLMProvider, LLMResponse

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)

    def _chat(self, messages: list[dict], temperature: float) -> tuple[str, float]:
        start = time.monotonic()
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
                timeout=120.0,
            )
            response.raise_for_status()
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Start Ollama and run: ollama pull llama3.1:8b"
            )
        latency_ms = (time.monotonic() - start) * 1000
        data = response.json()
        content = data["message"]["content"]
        return content, latency_ms

    def complete(self, system: str, user: str, temperature: float = 0.3) -> LLMResponse:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        content, latency_ms = self._chat(messages, temperature)
        return LLMResponse(
            content=content,
            provider="ollama",
            model=self.model,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
        )

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: Type[BaseModel],
        temperature: float = 0.1,
    ) -> tuple[BaseModel, LLMResponse]:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_system = (
            f"{system}\n\n"
            f"You MUST respond with valid JSON that exactly matches this schema:\n"
            f"{schema_json}\n\n"
            "Respond with only the JSON object, no markdown, no explanation."
        )
        messages = [
            {"role": "system", "content": structured_system},
            {"role": "user", "content": user},
        ]
        content, latency_ms = self._chat(messages, temperature)

        clean = content.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1]) if len(lines) > 2 else clean

        parsed = schema.model_validate_json(clean)
        resp = LLMResponse(
            content=content,
            provider="ollama",
            model=self.model,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
        )
        return parsed, resp
