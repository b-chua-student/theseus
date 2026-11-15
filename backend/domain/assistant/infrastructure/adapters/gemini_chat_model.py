import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.models.entities import Exchange
from domain.assistant.models.errors import ChatModelError, ChatModelRateLimitedError
from domain.assistant.models.value_objects import Answer, Query, RetrievedChunk

DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_TIMEOUT_MS = 30_000


class GeminiChatModel(ChatModel):
    """ChatModel adapter backed by the Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        system_instruction: str | None = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        load_dotenv()
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is not set")

        self._client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=timeout_ms))
        self._model = model
        self._config = types.GenerateContentConfig(system_instruction=system_instruction)

    def reply(
        self,
        history: list[Exchange],
        query: Query,
        context: list[RetrievedChunk] | None = None,
    ) -> Answer:
        contents: list[types.Content] = []

        for exchange in history:
            contents.append(self._turn("user", exchange.query.text))
            if exchange.answer is not None:
                contents.append(self._turn("model", exchange.answer.text))

        contents.append(self._turn("user", self._with_context(query.text, context)))

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=self._config,
            )
        except genai_errors.APIError as exc:
            if exc.code == 429:
                raise ChatModelRateLimitedError(
                    "The AI provider is rate limiting requests."
                ) from exc
            raise ChatModelError(f"The AI provider returned an error ({exc.code}).") from exc
        except Exception as exc:  # network failures, timeouts, SDK errors
            raise ChatModelError("Could not reach the AI provider.") from exc

        # Blocked or empty candidates yield no text; surface that as a model error
        # rather than crashing on the Answer invariant.
        text = (response.text or "").strip()
        if not text:
            raise ChatModelError("The AI provider returned an empty response.")

        return Answer(text)

    @staticmethod
    def _with_context(text: str, context: list[RetrievedChunk] | None) -> str:
        if not context:
            return text
        sources = "\n\n".join(f"[{i}] ({c.location}) {c.text}" for i, c in enumerate(context, 1))
        return (
            "Use the following excerpts from the user's sources when relevant.\n\n"
            f"Sources:\n{sources}\n\nQuestion: {text}"
        )

    @staticmethod
    def _turn(role: str, text: str) -> types.Content:
        return types.Content(role=role, parts=[types.Part(text=text)])
