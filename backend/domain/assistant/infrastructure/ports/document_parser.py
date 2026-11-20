from abc import ABC, abstractmethod


class DocumentParser(ABC):
    """Port for converting raw source text into structured text for chunking."""

    @abstractmethod
    def parse(self, raw_text: str) -> str:
        """Return the structured text parsed from ``raw_text``."""
