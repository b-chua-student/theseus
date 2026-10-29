import os

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from domain.conversation.entities import Exchange
from ports.generation.answer_generator import AnswerGenerator
from ports.generation.errors import (
    GenerationProviderError,
    GenerationTimeoutError,
    MalformedAnswerError,
)
from ports.retrieval.retriever import RetrievedPassage

SYSTEM_INSTRUCTION = (
    "You answer questions about a manuscript. Use only the numbered passages "
    "provided. If they do not contain the answer, say so plainly. "
    "Cite passages inline as [1], [2]. Do not invent facts."
)


class GeminiAnswerGenerator(AnswerGenerator):
    """Answer generator backed by the Gemini API."""

    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        api_key: str | None = None,
        timeout_ms: int = 30_000,
    ) -> None:
        self._model_name = model_name
        self._client = genai.Client(
            api_key=api_key or os.environ["GEMINI_API_KEY"],
            http_options=types.HttpOptions(timeout=timeout_ms),
        )

    def generate(
        self,
        query: str,
        passages: list[RetrievedPassage],
        history: list[Exchange],
    ) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=self._build_prompt(query, passages, history),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                ),
            )
        except genai_errors.APIError as exc:
            raise GenerationProviderError(str(exc)) from exc
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise GenerationTimeoutError("Gemini timed out") from exc

        text = response.text
        if not text or not text.strip():
            raise MalformedAnswerError("Gemini returned an empty answer")
        return text.strip()

    @staticmethod
    def _build_prompt(
        query: str,
        passages: list[RetrievedPassage],
        history: list[Exchange],
    ) -> str:
        passage_block = "\n\n".join(
            f"[{index}] {passage.text}" for index, passage in enumerate(passages, start=1)
        )

        history_lines: list[str] = []
        for exchange in history:
            if exchange.answer is not None:
                history_lines.append(f"User: {exchange.query.content}")
                history_lines.append(f"Assistant: {exchange.answer.content}")
        history_block = "\n".join(history_lines) or "(none)"

        return (
            f"Passages:\n{passage_block}\n\n"
            f"Conversation so far:\n{history_block}\n\n"
            f"Question: {query}"
        )
