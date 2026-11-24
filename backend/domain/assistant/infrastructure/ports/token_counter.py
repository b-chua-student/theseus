from abc import ABC, abstractmethod


class TokenCounter(ABC):
    """Port for measuring how many model tokens a text takes."""

    @abstractmethod
    def count(self, text: str) -> int:
        """Return the number of tokens ``text`` takes in the chat model's context window."""
