"""In-memory pass-through document parser.

Manuscript section bodies are already plain text, so the default parser simply
returns the raw text unchanged. Production deployments should swap in a real
parser (e.g. a markdown or PDF parser) via the container.
"""

from domain.assistant.infrastructure.ports.document_parser import DocumentParser


class InMemoryDocumentParser(DocumentParser):
    """Returns raw text unchanged — a no-op parser for the default pipeline."""

    def parse(self, raw_text: str) -> str:
        return raw_text
