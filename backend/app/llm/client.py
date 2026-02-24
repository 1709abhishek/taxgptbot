from typing import List, Dict, Any, Optional
from anthropic import Anthropic

from app.config import get_settings


class ClaudeClient:
    """Wrapper for Anthropic Claude API."""

    # Available models (newest first)
    MODELS = {
        "opus": "claude-opus-4-5-20251101",      # Best quality, highest cost
        "sonnet": "claude-sonnet-4-20250514",   # Good balance
        "haiku": "claude-haiku-3-5-20241022",   # Fastest, lowest cost
    }

    def __init__(self, model: str = None):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        # Use model from settings, or default to sonnet
        self.default_model = model or getattr(settings, 'llm_model', self.MODELS["sonnet"])

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = None,
        model: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """Send a chat message and get a response."""
        kwargs = {
            "model": model or self.default_model,
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
