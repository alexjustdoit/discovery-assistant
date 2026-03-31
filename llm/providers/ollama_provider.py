from __future__ import annotations

import json
import os
import re
import time
from typing import Type

import httpx
from pydantic import BaseModel

from llm.providers.base import LLMProvider, LLMResponse

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "phi4"):
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
                "Start Ollama and run: ollama pull phi4"
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

    @staticmethod
    def _schema_to_example(schema: Type[BaseModel]) -> str:
        """Build a simple example JSON from a Pydantic model.

        Avoids dumping the raw $defs/$ref schema, which causes local models
        to echo the schema definition back instead of returning actual data.
        """
        raw = schema.model_json_schema()
        defs = raw.get("$defs", {})

        def resolve(s: dict) -> object:
            if "$ref" in s:
                name = s["$ref"].split("/")[-1]
                return resolve(defs.get(name, {}))
            t = s.get("type")
            if t == "string":
                return "..."
            if t == "boolean":
                return True
            if t == "integer":
                return 0
            if t == "array":
                return [resolve(s.get("items", {}))]
            if t == "object" or "properties" in s:
                return {k: resolve(v) for k, v in s.get("properties", {}).items()}
            return "..."

        return json.dumps(resolve(raw), indent=2)

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: Type[BaseModel],
        temperature: float = 0.1,
    ) -> tuple[BaseModel, LLMResponse]:
        example = self._schema_to_example(schema)
        structured_system = (
            f"{system}\n\n"
            f"Respond with a JSON object in exactly this format:\n"
            f"{example}\n\n"
            "Return only the JSON object with real values — no markdown, no explanation."
        )
        messages = [
            {"role": "system", "content": structured_system},
            {"role": "user", "content": user},
        ]
        content, latency_ms = self._chat(messages, temperature)

        clean = content.strip()

        # Extract from markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if fence_match:
            clean = fence_match.group(1).strip()
        else:
            # Find the outermost JSON object in case the model added prose around it
            obj_match = re.search(r"\{[\s\S]*\}", clean)
            if obj_match:
                clean = obj_match.group()

        parsed = schema.model_validate_json(clean)
        resp = LLMResponse(
            content=content,
            provider="ollama",
            model=self.model,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
        )
        return parsed, resp
