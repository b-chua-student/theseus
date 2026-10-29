class GenerationError(Exception):
    """Base error for answer generation."""


class GenerationTimeoutError(GenerationError):
    """The provider did not respond in time."""


class GenerationProviderError(GenerationError):
    """The provider returned an error."""


class MalformedAnswerError(GenerationError):
    """The provider returned an unusable answer."""
