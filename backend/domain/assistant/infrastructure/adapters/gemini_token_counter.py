"""Token counter backed by the Gemini ``count_tokens`` API.

Counts are cached per text, since the same passages are measured on many requests. If the
provider cannot be reached, a deliberately high estimate is used, and not cached, so a request
never exceeds the context window because of a counting outage.
"""

import logging
import os
from typing import Protocol

from dotenv import load_dotenv
from google import genai
from google.genai import types

from domain.assistant.infrastructure.ports.token_counter import TokenCounter

logger = logging.getLogger(__name__)

DEFAULT_COUNT_MODEL = "gemini-3-flash-preview"
DEFAULT_TIMEOUT_MS = 10_000
CACHE_SIZE = 8192


class CountModels(Protocol):
    """The part of ``genai.Client.models`` this adapter uses."""

    def count_tokens(self, *, model: str, contents: str) -> types.CountTokensResponse:
        """Count the tokens of ``contents``."""
        ...


class CountClient(Protocol):
    """The part of ``genai.Client`` this adapter uses."""

    @property
    def models(self) -> CountModels:
        """Return the models API."""
        ...


def estimate_tokens(text: str) -> int:
    """Return a high estimate of the tokens in ``text``, at one token per two characters."""
    return len(text) // 2 + 1


class GeminiTokenCounter(TokenCounter):
    """TokenCounter that asks the Gemini API, falling back to a high estimate."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_COUNT_MODEL,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        client: CountClient | None = None,
    ) -> None:
        """Configure the client and model.

        Raises:
            ValueError: If no client is given and GEMINI_API_KEY is not set.
        """
        if client is None:
            load_dotenv()
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY is not set")
            client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=timeout_ms))
        self._client = client
        self._model = model
        self._cache: dict[str, int] = {}

    def count(self, text: str) -> int:
        """Return the token count of ``text``, or a high estimate if the provider fails."""
        if not text:
            return 0
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        try:
            response = self._client.models.count_tokens(model=self._model, contents=text)
        except Exception:  # network failures, timeouts, SDK errors
            logger.warning("GeminiTokenCounter: counting failed; using an estimate", exc_info=True)
            return estimate_tokens(text)
        total = response.total_tokens
        if total is None:
            return estimate_tokens(text)
        if len(self._cache) >= CACHE_SIZE:
            self._cache.clear()
        self._cache[text] = total
        return total
