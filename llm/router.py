from __future__ import annotations

import os

from llm.providers.base import LLMProvider


class LLMRouter:
    """
    Routes to local (Ollama) or API providers based on env config.

    USE_LOCAL_LLM=true  → OllamaProvider (free, requires local Ollama)
    USE_LOCAL_LLM=false → OpenAIProvider (gpt-5.4-nano) or ClaudeProvider (quality tasks)
    """

    DEFAULT_LOCAL_MODEL = "llama3.1:8b"
    DEFAULT_CHEAP_API = "gpt-5.4-nano"
    DEFAULT_QUALITY_API = "claude-haiku-4-5-20251001"

    def get_provider(self, quality_required: bool = False) -> LLMProvider:
        use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"

        if use_local:
            from llm.providers.ollama_provider import OllamaProvider
            return OllamaProvider(model=self.DEFAULT_LOCAL_MODEL)

        if quality_required and os.getenv("ANTHROPIC_API_KEY"):
            from llm.providers.claude_provider import ClaudeProvider
            return ClaudeProvider(model=self.DEFAULT_QUALITY_API)

        from llm.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(model=self.DEFAULT_CHEAP_API)


router = LLMRouter()
