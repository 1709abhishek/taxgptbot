from typing import List, Dict, Any, Optional

from app.config import get_settings


class LLMClient:
    """Unified wrapper for LLM APIs (OpenAI and Anthropic)."""

    # OpenAI models
    OPENAI_MODELS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4-turbo",
    }

    # Anthropic models
    ANTHROPIC_MODELS = {
        "opus": "claude-opus-4-5-20251101",
        "sonnet": "claude-sonnet-4-20250514",
        "haiku": "claude-haiku-3-5-20241022",
    }

    def __init__(self, provider: str = None, model: str = None):
        settings = get_settings()
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.anthropic_api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = None,
        model: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """Send a chat message and get a response."""
        model = model or self.model

        if self.provider == "openai":
            return self._chat_openai(messages, system, model, max_tokens, temperature)
        else:
            return self._chat_anthropic(messages, system, model, max_tokens, temperature)

    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Send chat via OpenAI API."""
        formatted_messages = []

        # Add system message if provided
        if system:
            formatted_messages.append({"role": "system", "content": system})

        # Add user/assistant messages
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        response = self.client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content

    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Send chat via Anthropic API."""
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        if temperature > 0:
            kwargs["temperature"] = temperature

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def complete(
        self,
        prompt: str,
        system: str = None,
        model: str = None,
        max_tokens: int = 4096,
    ) -> str:
        """Simple completion with a single prompt."""
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            model=model,
            max_tokens=max_tokens,
        )


# Backwards compatibility alias
ClaudeClient = LLMClient
